const API_BASE = "http://localhost:8080";
const LEADER_BASE = "http://localhost:9000";

async function fetchJson(url, options = {}) {
  const response = await fetch(url, options);

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText);
  }

  return response.json();
}

async function loadLeader() {
  try {
    const leader = await fetchJson(`${LEADER_BASE}/leader`);
    document.getElementById("leaderId").innerText =
      leader.leader_id ?? "Belum ada leader";

    const logs = await fetchJson(`${LEADER_BASE}/logs`);
    const lastLogs = logs.data
      .slice(-8)
      .map((item) => `[${item.time}] ${item.message}`)
      .join("\n");
    document.getElementById("leaderLog").innerText =
      lastLogs || "Belum ada log election.";
  } catch (error) {
    document.getElementById("leaderId").innerText = "Error";
    document.getElementById("leaderLog").innerText = error.message;
  }
}

async function startElection() {
  try {
    await fetchJson(`${LEADER_BASE}/election/start`, {
      method: "POST",
    });
    await loadLeader();
    await loadAssignments();
  } catch (error) {
    alert("Gagal menjalankan election: " + error.message);
  }
}

async function failNode50() {
  try {
    await fetchJson(`${LEADER_BASE}/nodes/50/fail`, {
      method: "POST",
    });

    await fetchJson(`${LEADER_BASE}/election/start`, {
      method: "POST",
    });

    await loadLeader();
  } catch (error) {
    alert("Gagal mematikan node 50: " + error.message);
  }
}

async function recoverNode50() {
  try {
    await fetchJson(`${LEADER_BASE}/nodes/50/recover`, {
      method: "POST",
    });

    await fetchJson(`${LEADER_BASE}/election/start`, {
      method: "POST",
    });

    await loadLeader();
  } catch (error) {
    alert("Gagal mengaktifkan node 50: " + error.message);
  }
}

async function createTicket() {
  const payload = {
    user_id: Number(document.getElementById("userId").value),
    title: document.getElementById("title").value,
    description: document.getElementById("description").value,
    category: document.getElementById("category").value,
    priority: document.getElementById("priority").value,
  };

  if (!payload.title || !payload.description) {
    alert("Judul dan deskripsi wajib diisi.");
    return;
  }

  try {
    const result = await fetchJson(`${API_BASE}/tickets`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    document.getElementById("createStatus").innerText =
      `Ticket #${result.data.id} berhasil dibuat melalui ${result.instance}`;

    document.getElementById("title").value = "";
    document.getElementById("description").value = "";

    setTimeout(loadAllData, 1200);
  } catch (error) {
    document.getElementById("createStatus").innerText = "Gagal membuat ticket.";
    alert(error.message);
  }
}

async function loadTickets() {
  const result = await fetchJson(`${API_BASE}/tickets`);
  const table = document.getElementById("ticketTable");

  table.innerHTML = "";

  result.data.forEach((ticket) => {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>${ticket.id}</td>
            <td>${ticket.user_name}</td>
            <td>${ticket.title}</td>
            <td>${ticket.category}</td>
            <td>${ticket.priority}</td>
            <td>${ticket.status}</td>
            <td>${result.instance}</td>
        `;

    table.appendChild(row);
  });
}

async function loadAssignments() {
  const result = await fetchJson(`${API_BASE}/assignments`);
  const table = document.getElementById("assignmentTable");

  table.innerHTML = "";

  result.data.forEach((item) => {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>${item.id}</td>
            <td>#${item.ticket_id} - ${item.ticket_title}</td>
            <td>${item.admin_name}</td>
            <td>${item.assigned_by_leader_id}</td>
            <td>${item.created_at}</td>
        `;

    table.appendChild(row);
  });
}

async function loadNotifications() {
  const result = await fetchJson(`${API_BASE}/notifications`);
  const table = document.getElementById("notificationTable");

  table.innerHTML = "";

  result.data.forEach((item) => {
    const row = document.createElement("tr");

    row.innerHTML = `
            <td>${item.id}</td>
            <td>${item.user_name}</td>
            <td>${item.ticket_id ?? "-"}</td>
            <td>${item.message}</td>
            <td>${item.created_at}</td>
        `;

    table.appendChild(row);
  });
}

async function loadAllData() {
  await loadLeader();
  await loadTickets();
  await loadAssignments();
  await loadNotifications();
}

loadAllData();

setInterval(loadAllData, 5000);
