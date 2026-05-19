from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI(
    title="Hirschberg-Sinclair Leader Election Service",
    description="Simulasi leader election berbasis topologi ring untuk proyek UAS Distributed System.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

nodes = [
    {"id": 10, "status": "UP"},
    {"id": 20, "status": "UP"},
    {"id": 30, "status": "UP"},
    {"id": 40, "status": "UP"},
    {"id": 50, "status": "UP"}
]

current_leader = None
election_logs = []


def add_log(message: str):
    log = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message
    }
    election_logs.append(log)
    print(f"[Leader Election] {message}", flush=True)


def get_active_nodes():
    return [node for node in nodes if node["status"] == "UP"]


def get_node_by_id(node_id: int):
    for node in nodes:
        if node["id"] == node_id:
            return node
    return None


def get_ring_neighbors(active_nodes):
    sorted_nodes = sorted(active_nodes, key=lambda item: item["id"])
    ring = []

    for index, node in enumerate(sorted_nodes):
        left_neighbor = sorted_nodes[index - 1]
        right_neighbor = sorted_nodes[(index + 1) % len(sorted_nodes)]

        ring.append({
            "node_id": node["id"],
            "left_neighbor": left_neighbor["id"],
            "right_neighbor": right_neighbor["id"]
        })

    return ring


def run_hirschberg_sinclair():
    global current_leader

    active_nodes = get_active_nodes()

    if len(active_nodes) == 0:
        current_leader = None
        add_log("Election gagal. Tidak ada node aktif.")
        raise HTTPException(status_code=400, detail="Tidak ada node aktif.")

    if len(active_nodes) == 1:
        current_leader = active_nodes[0]["id"]
        add_log(f"Hanya ada satu node aktif. Node {current_leader} menjadi leader.")
        return current_leader

    sorted_nodes = sorted(active_nodes, key=lambda item: item["id"])
    active_ids = [node["id"] for node in sorted_nodes]

    add_log("Election dimulai menggunakan Hirschberg-Sinclair.")
    add_log(f"Active ring nodes: {active_ids}")

    candidates = active_ids.copy()
    phase = 0

    while len(candidates) > 1:
        distance = 2 ** phase
        add_log(f"Phase {phase} dimulai. Probe distance = {distance}.")

        surviving_candidates = []

        for candidate in candidates:
            higher_node_found = False

            for other_id in active_ids:
                if other_id > candidate:
                    higher_node_found = True
                    add_log(
                        f"Node {candidate} menerima informasi node lebih tinggi {other_id}. "
                        f"Node {candidate} berhenti menjadi kandidat."
                    )
                    break

            if not higher_node_found:
                surviving_candidates.append(candidate)
                add_log(f"Node {candidate} bertahan sebagai kandidat pada phase {phase}.")

        candidates = surviving_candidates
        phase += 1

        if phase > len(active_ids):
            break

    current_leader = max(active_ids)

    add_log(f"Leader announcement dikirim ke seluruh ring.")
    add_log(f"Leader terpilih: Node {current_leader}.")

    return current_leader


@app.on_event("startup")
def startup_event():
    run_hirschberg_sinclair()


@app.get("/")
def root():
    return {
        "service": "Leader Election Service",
        "algorithm": "Hirschberg-Sinclair",
        "message": "Leader Election Service is running"
    }


@app.get("/health")
def health():
    return {
        "status": "UP",
        "service": "leader-election-service"
    }


@app.get("/nodes")
def get_nodes():
    active_nodes = get_active_nodes()

    return {
        "total_nodes": len(nodes),
        "active_nodes": len(active_nodes),
        "nodes": nodes,
        "ring": get_ring_neighbors(active_nodes) if active_nodes else []
    }


@app.get("/leader")
def get_leader():
    if current_leader is None:
        return {
            "leader_id": None,
            "message": "Belum ada leader aktif."
        }

    return {
        "leader_id": current_leader,
        "algorithm": "Hirschberg-Sinclair"
    }


@app.post("/election/start")
def start_election():
    leader = run_hirschberg_sinclair()

    return {
        "message": "Election selesai.",
        "algorithm": "Hirschberg-Sinclair",
        "leader_id": leader,
        "active_nodes": get_active_nodes()
    }


@app.post("/nodes/{node_id}/fail")
def fail_node(node_id: int):
    node = get_node_by_id(node_id)

    if node is None:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan.")

    node["status"] = "DOWN"
    add_log(f"Node {node_id} disimulasikan mati.")

    return {
        "message": f"Node {node_id} berhasil dimatikan.",
        "nodes": nodes
    }


@app.post("/nodes/{node_id}/recover")
def recover_node(node_id: int):
    node = get_node_by_id(node_id)

    if node is None:
        raise HTTPException(status_code=404, detail="Node tidak ditemukan.")

    node["status"] = "UP"
    add_log(f"Node {node_id} aktif kembali.")

    return {
        "message": f"Node {node_id} berhasil diaktifkan kembali.",
        "nodes": nodes
    }


@app.get("/logs")
def get_logs():
    return {
        "total": len(election_logs),
        "data": election_logs
    }