from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from ws_manager import ConnectionManager
from orchestrator import TravelOrchestrator
from llm_client import LLMClient
from database import init_db, save_itinerary, get_latest_itinerary, get_all_itineraries

app = FastAPI(title="旅行管家")
manager = ConnectionManager()
llm = LLMClient()
orchestrator = TravelOrchestrator(llm)

current_plan = {"days": []}

init_db()

app.mount("/static", StaticFiles(directory=r"C:\Users\21171\ClaudeCodeProjects\旅行管家"), name="static")


@app.get("/")
async def get():
    with open("travel-butler.html", encoding="utf-8") as f:
        html = f.read()
    return HTMLResponse(content=html)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            if msg_type == "generate_plan":
                params = data["data"]
                result = await orchestrator.run_plan_generation(websocket, params)
                current_plan["days"] = result.get("days", [])
                if current_plan["days"]:
                    save_itinerary(
                        params.get("destination", ""),
                        params.get("start_date", ""),
                        params.get("days", 0),
                        result,
                    )

            elif msg_type == "trigger_emergency":
                new_plan = await orchestrator.run_emergency_replanning(
                    websocket, data["data"]["scenario"], current_plan,
                    custom_desc=data["data"].get("custom_desc", "")
                )
                if new_plan:
                    current_plan["days"] = new_plan.get("days", [])

            elif msg_type == "refresh_prices":
                await orchestrator.run_price_refresh(
                    websocket, data["data"]["destination"]
                )

            elif msg_type == "load_plan":
                saved = get_latest_itinerary()
                if saved:
                    current_plan["days"] = saved.get("days", [])
                    await websocket.send_json({"type": "plan_result", "data": saved})

            elif msg_type == "get_history":
                history = get_all_itineraries()
                await websocket.send_json({"type": "history_list", "data": history})

            elif msg_type == "update_plan":
                plan = data["data"]["plan"]
                current_plan["days"] = plan.get("days", [])
                save_itinerary("", "", len(plan.get("days", [])), plan)
                await websocket.send_json({"type": "plan_result", "data": plan})

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
        manager.disconnect(websocket)
