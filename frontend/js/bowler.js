const API = "http://127.0.0.1:5000/api";
const COLORS = ["#e63946", "#2196f3", "#4caf50", "#ff9800", "#9c27b0"];

let selectedBowlers = [];
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
    const res = await fetch(`${API}/bowlers?q=${q}`);
    const bowlers = await res.json();
    box.innerHTML = bowlers
      .map(
        (b) =>
          `<div class="suggestion-item" onclick="addBowler('${b.id}', '${b.display}')">${b.display}</div>`,
      )
      .join("");
  });

function addBowler(id, display) {
  if (selectedBowlers.find((b) => b.id === id)) return;
  if (selectedBowlers.length >= 5) {
    alert("Maximum 5 bowlers allowed");
    return;
  }
  selectedBowlers.push({ id, display });
  renderTags();
  document.getElementById("searchInput").value = "";
  document.getElementById("suggestions").innerHTML = "";
}

function removeBowler(id) {
  selectedBowlers = selectedBowlers.filter((b) => b.id !== id);
  renderTags();
  if (document.getElementById("resultsSection").style.display !== "none") {
    if (selectedBowlers.length === 0) {
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
  const container = document.getElementById("selectedBowlers");
  container.innerHTML = selectedBowlers
    .map(
      (b, i) =>
        `<div class="player-tag" style="background:${COLORS[i]}">
      ${b.display}
      <span class="remove" onclick="removeBowler('${b.id}')">×</span>
    </div>`,
    )
    .join("");
}

function formatName(name) {
  return name
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(" ");
}

async function fetchAndRender() {
  const season = document.getElementById("seasonSelect").value;
  const params = selectedBowlers
    .map((b) => `bowlers=${encodeURIComponent(b.id)}`)
    .join("&");
  const url = `${API}/compare_bowlers?${params}&season=${season}`;
  const res = await fetch(url);
  const data = await res.json();
  renderTable(data);
  renderRadar(data);
}

document
  .getElementById("compareBtn")
  .addEventListener("click", async function () {
    if (selectedBowlers.length < 1) {
      alert("Please add at least 1 bowler");
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
      selectedBowlers.length > 0
    ) {
      await fetchAndRender();
    }
  });

function renderTable(data) {
  const body = document.getElementById("statsBody");
  body.innerHTML = data
    .map(
      (b, i) => `
    <tr>
      <td class="player-name-cell" style="color:${COLORS[i]}">${b.display_name}</td>
      <td>${b.economy}</td>
      <td>${b.dot_pct}%</td>
      <td>${b.bowling_sr}</td>
      <td>${b.wickets}</td>
      <td>${b.death_economy}</td>
      <td>${b.wkts_vs_rhb}%</td>
      <td>${b.wkts_vs_lhb}%</td>
      <td>${b.innings}</td>
    </tr>
  `,
    )
    .join("");
}

function renderRadar(data) {
  const labels = [
    "Economy",
    "Dot %",
    "Bowling SR",
    "Wickets",
    "Death Eco",
    "Wkt% RHB",
    "Wkt% LHB",
  ];
  const datasets = data.map((b, i) => ({
    label: b.display_name,
    data: [
      b.economy_pct,
      b.dot_pct_pct,
      b.bowling_sr_pct,
      b.wickets_pct,
      b.death_economy_pct,
      b.wkts_vs_rhb_pct,
      b.wkts_vs_lhb_pct,
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
