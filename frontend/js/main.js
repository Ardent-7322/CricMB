const API = "http://127.0.0.1:5000/api";
const COLORS = ["#e63946", "#2196f3", "#4caf50", "#ff9800", "#9c27b0"];

let selectedPlayers = [];
let radarChart = null;

async function loadSeasons() {
  const res = await fetch(`${API}/seasons`);
  const seasons = await res.json();
  const select = document.getElementById("seasonSelect");
  seasons.reverse().forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = `IPL ${s}`;
    select.appendChild(opt);
  });
}
document
  .getElementById("searchInput")
  .addEventListener("input", async function () {
    const q = this.value.trim();
    const box = document.getElementById("suggestions");
    if (q.length < 2) {
      box.innerHTML = "";
      return;
    }
    const res = await fetch(`${API}/players?q=${q}`);
    const players = await res.json();
    box.innerHTML = players
      .map(
        (p) =>
          `<div class="suggestion-item" onclick="addPlayer('${p.id}', '${p.display}')">${p.display}</div>`,
      )
      .join("");
  });

function addPlayer(id, display) {
  if (selectedPlayers.find((p) => p.id === id)) return;
  if (selectedPlayers.length >= 5) {
    alert("Maximum 5 players allowed");
    return;
  }
  selectedPlayers.push({ id, display });
  renderTags();
  document.getElementById("searchInput").value = "";
  document.getElementById("suggestions").innerHTML = "";
}

function removePlayer(id) {
  selectedPlayers = selectedPlayers.filter((p) => p.id !== id);
  renderTags();
  if (document.getElementById("resultsSection").style.display !== "none") {
    if (selectedPlayers.length === 0) {
      document.getElementById("resultsSection").style.display = "none";
      if (radarChart) {
        radarChart.destroy();
        radarChart = null;
      }
    } else {
      fetchAndRender();
    }
  }
}

function renderTags() {
  const container = document.getElementById("selectedPlayers");
  container.innerHTML = selectedPlayers
    .map(
      (p, i) =>
        `<div class="player-tag" style="background:${COLORS[i]}">
      ${p.display}
      <span class="remove" onclick="removePlayer('${p.id}')">×</span>
    </div>`,
    )
    .join("");
}

async function fetchAndRender() {
  const season = document.getElementById("seasonSelect").value;
  const params = selectedPlayers
    .map((p) => `players=${encodeURIComponent(p.id)}`)
    .join("&");
  const url = `${API}/compare?${params}&season=${season}`;
  const res = await fetch(url);
  const data = await res.json();
  renderTable(data);
  renderRadar(data);
}

document
  .getElementById("compareBtn")
  .addEventListener("click", async function () {
    if (selectedPlayers.length < 1) {
      alert("Please add at least 1 player");
      return;
    }
    await fetchAndRender();
    document.getElementById("resultsSection").style.display = "block";
  });

document
  .getElementById("seasonSelect")
  .addEventListener("change", async function () {
    if (
      document.getElementById("resultsSection").style.display !== "none" &&
      selectedPlayers.length > 0
    ) {
      await fetchAndRender();
    }
  });

function renderTable(data) {
  const body = document.getElementById("statsBody");
  body.innerHTML = data
    .map(
      (p, i) => `
    <tr>
      <td class="player-name-cell" style="color:${COLORS[i]}">${p.display_name}</td>
      <td>${p.powerplay_sr}</td>
      <td>${p.death_sr}</td>
      <td>${p.dot_pct}%</td>
      <td>${p.pace_sr}</td>
      <td>${p.spin_sr}</td>
      <td>${p.death_bpb}</td>
      <td>${p.total_runs}</td>
      <td>${p.innings}</td>
    </tr>
  `,
    )
    .join("");
}

function renderRadar(data) {
  const labels = [
    "Powerplay SR",
    "Death SR",
    "Pace SR",
    "Spin SR",
    "Total Runs",
    "Dot %",
    "Death BpB",
  ];
  const datasets = data.map((p, i) => ({
    label: p.display_name,
    data: [
      p.powerplay_sr_pct,
      p.death_sr_pct,
      p.pace_sr_pct,
      p.spin_sr_pct,
      p.total_runs_pct,
      p.dot_pct_pct,
      p.death_bpb_pct,
    ],
    borderColor: COLORS[i],
    backgroundColor: COLORS[i] + "33",
    borderWidth: 2,
    pointBackgroundColor: COLORS[i],
  }));

  if (radarChart) radarChart.destroy();

  radarChart = new Chart(document.getElementById("radarChart"), {
    type: "radar",
    data: { labels, datasets },
    options: {
      responsive: true,
      plugins: { legend: { position: "top" } },
      scales: {
        r: {
          min: 0,
          max: 100,
          ticks: { stepSize: 25, font: { size: 10 } },
          pointLabels: { font: { size: 12 } },
        },
      },
    },
  });
}

loadSeasons();
