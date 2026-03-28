const API = "http://127.0.0.1:5000/api";
const COLORS = ["#e63946", "#2196f3", "#4caf50", "#ff9800", "#9c27b0"];
const usedColors = new Set();

let selectedTeams = [];
let radarChart = null;
let allTeams = [];

function getNextColor() {
  for (let color of COLORS) {
    if (!usedColors.has(color)) {
      usedColors.add(color);
      return color;
    }
  }
  return COLORS[0];
}

async function loadTeams() {
  const res = await fetch(`${API}/teams`);
  allTeams = await res.json();
}

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

document.getElementById("searchInput").addEventListener("input", function () {
  const q = this.value.trim().toLowerCase();
  const box = document.getElementById("suggestions");
  if (q.length < 1) {
    box.innerHTML = "";
    return;
  }
  const matched = allTeams.filter((t) => t.toLowerCase().includes(q));
  box.innerHTML = matched
    .map(
      (t) =>
        `<div class="suggestion-item" onclick="addTeam('${t}')">${t}</div>`,
    )
    .join("");
});

function addTeam(name) {
  if (selectedTeams.find((t) => t.name === name)) return;
  if (selectedTeams.length >= 5) {
    alert("Maximum 5 teams allowed");
    return;
  }
  const color = getNextColor();
  selectedTeams.push({ name, color });
  renderTags();
  document.getElementById("searchInput").value = "";
  document.getElementById("suggestions").innerHTML = "";
}

function removeTeam(name) {
  const removed = selectedTeams.find((t) => t.name === name);
  if (removed) usedColors.delete(removed.color);
  selectedTeams = selectedTeams.filter((t) => t.name !== name);
  renderTags();
  if (document.getElementById("resultsSection").style.display !== "none") {
    if (selectedTeams.length === 0) {
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
  const container = document.getElementById("selectedTeams");
  container.innerHTML = selectedTeams
    .map(
      (t) =>
        `<div class="player-tag" style="background:${t.color}">
      ${t.name}
      <span class="remove" onclick="removeTeam('${t.name}')">×</span>
    </div>`,
    )
    .join("");
}

async function fetchAndRender() {
  const season = document.getElementById("seasonSelect").value;
  const params = selectedTeams
    .map((t) => `teams=${encodeURIComponent(t.name)}`)
    .join("&");
  const url = `${API}/compare_teams?${params}&season=${season}`;
  const res = await fetch(url);
  const data = await res.json();

  if (data.error) {
    alert(data.error);
    return;
  }

  renderTable(data);
  renderRadar(data);
}

document
  .getElementById("compareBtn")
  .addEventListener("click", async function () {
    if (selectedTeams.length < 2) {
      alert("Please add at least 2 teams");
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
      selectedTeams.length > 0
    ) {
      await fetchAndRender();
    }
  });

function renderTable(data) {
  const body = document.getElementById("statsBody");
  body.innerHTML = data
    .map((t) => {
      const team = selectedTeams.find((st) => st.name === t.name);
      const color = team ? team.color : "#999";
      return `
      <tr>
        <td><div class="player-name-cell" style="color:${color}">
          <span class="color-dot" style="background:${color}"></span>
          ${t.name}
        </div></td>
        <td>${t.win_pct}%</td>
        <td>${t.avg_1st_innings}</td>
        <td>${t.avg_2nd_innings}</td>
        <td>${t.home_win_pct}%</td>
        <td>${t.pp_avg}</td>
        <td>${t.death_runs_avg}</td>
        <td>${t.sixes_per_match}</td>
        <td>${t.wins}/${t.total_matches}</td>
      </tr>
    `;
    })
    .join("");
}

function renderRadar(data) {
  const labels = [
    "Win %",
    "Avg 1st Innings",
    "Avg 2nd Innings",
    "Home Win %",
    "Powerplay Avg",
    "Death Over Runs",
    "Sixes/Match",
  ];

  const datasets = data.map((t) => {
    const team = selectedTeams.find((st) => st.name === t.name);
    const color = team ? team.color : "#999";
    return {
      label: t.name,
      data: [
        t.win_pct_pct,
        t.avg_1st_innings_pct,
        t.avg_2nd_innings_pct,
        t.home_win_pct_pct,
        t.pp_avg_pct,
        t.death_runs_avg_pct,
        t.sixes_per_match_pct,
      ],
      borderColor: color,
      backgroundColor: color + "33",
      borderWidth: 2,
      pointBackgroundColor: color,
    };
  });

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

loadTeams();
loadSeasons();
