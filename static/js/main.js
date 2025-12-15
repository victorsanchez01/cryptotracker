//
//  main.js
//  CryptoTracker
//
//  Created by Cascade on Dec 14, 2025.
//  Copyright © 2025 CryptoTracker. All rights reserved.
//

const API_ROUTES = {
  LIST: "/api/cryptos",
  HISTORY: (id) => `/api/crypto/${id}/history`,
};

const REFRESH_INTERVAL_MS = 60000;

const formatters = {
  price: (value) => {
    if (value >= 1) {
      return `$${value.toLocaleString("en-US", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
      })}`;
    }
    return `$${value.toLocaleString("en-US", {
      minimumFractionDigits: 4,
      maximumFractionDigits: 4,
    })}`;
  },
  percent: (value) =>
    `${value > 0 ? "+" : ""}${value.toFixed(2)}%`,
  marketCap: (value) => {
    if (value >= 1_000_000_000) {
      return `${(value / 1_000_000_000).toFixed(2)}B`;
    }
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toFixed(2)}M`;
    }
    return value.toLocaleString("en-US");
  },
  volume: (value) => value.toLocaleString("en-US"),
};

const state = {
  cryptos: [],
  filtered: [],
  selectedCoin: null,
  refreshTimer: null,
  priceMap: new Map(),
  chart: null,
};

const elements = {
  grid: document.getElementById("cryptoGrid"),
  searchInput: document.getElementById("searchInput"),
  searchForm: document.getElementById("searchForm"),
  refreshButton: document.getElementById("refreshButton"),
  chartPanel: document.getElementById("chartPanel"),
  chartTitle: document.getElementById("chartTitle"),
  closeChartPanel: document.getElementById("closeChartPanel"),
  historyCanvas: document.getElementById("historyChart"),
  modalOverlay: document.getElementById("modalOverlay"),
  modalBody: document.getElementById("modalBody"),
  closeModal: document.getElementById("closeModal"),
};

const createSpinner = () => {
  const wrapper = document.createElement("div");
  wrapper.className = "loading-spinner";
  return wrapper;
};

const setGridContent = (content) => {
  elements.grid.innerHTML = "";
  if (content instanceof HTMLElement) {
    elements.grid.appendChild(content);
    return;
  }
  const placeholder = document.createElement("div");
  placeholder.className = "table-row";
  placeholder.textContent = content;
  elements.grid.appendChild(placeholder);
};

const animatePriceChange = (row, previous, current) => {
  if (previous == null || previous === current || !row.animate) {
    return;
  }
  const isUp = current > previous;
  row.animate(
    [
      { boxShadow: "0 0 0 rgba(0,0,0,0)" },
      {
        boxShadow: `0 0 25px ${isUp ? "rgba(0,208,156,0.35)" : "rgba(255,107,107,0.35)"}`,
      },
      { boxShadow: "0 0 0 rgba(0,0,0,0)" },
    ],
    { duration: 600, easing: "ease-out" }
  );
};

const buildRow = (coin, index) => {
  const row = document.createElement("div");
  row.className = "table-row fade-in";
  row.dataset.coinId = coin.id;
  row.innerHTML = `
    <span>${index + 1}</span>
    <span class="crypto-name">
      <img src="${coin.image}" alt="${coin.name}" loading="lazy" />
      <span>
        ${coin.name}
        <small>${coin.symbol.toUpperCase()}</small>
      </span>
    </span>
    <span data-field="price">${formatters.price(coin.current_price)}</span>
    <span class="${
      coin.price_change_percentage_24h >= 0 ? "value-positive" : "value-negative"
    }">${formatters.percent(coin.price_change_percentage_24h)}</span>
    <span>${
      formatters.marketCap(coin.market_cap)
    }</span>
    <span>${formatters.volume(coin.total_volume)}</span>
  `;
  row.addEventListener("click", () => handleCoinSelection(coin));
  const previousPrice = state.priceMap.get(coin.id);
  animatePriceChange(row, previousPrice, coin.current_price);
  state.priceMap.set(coin.id, coin.current_price);
  return row;
};

const renderCryptoList = () => {
  if (!state.filtered.length) {
    setGridContent("No se encontraron criptomonedas.");
    return;
  }
  elements.grid.innerHTML = "";
  const fragment = document.createDocumentFragment();
  state.filtered.forEach((coin, index) => {
    fragment.appendChild(buildRow(coin, index));
  });
  elements.grid.appendChild(fragment);
};

const filterCryptos = () => {
  const query = elements.searchInput.value.trim().toLowerCase();
  if (!query) {
    state.filtered = [...state.cryptos];
  } else {
    state.filtered = state.cryptos.filter(
      (coin) =>
        coin.name.toLowerCase().includes(query) ||
        coin.symbol.toLowerCase().includes(query)
    );
  }
  renderCryptoList();
};

const fetchJSON = async (url) => {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json();
};

const loadCryptos = async ({ showLoader = true } = {}) => {
  if (showLoader) {
    setGridContent(createSpinner());
  }
  try {
    const payload = await fetchJSON(API_ROUTES.LIST);
    state.cryptos = payload.data || [];
    filterCryptos();
  } catch (error) {
    if (!state.cryptos.length) {
      setGridContent("No pudimos cargar los datos. Intenta nuevamente.");
    }
  }
};

const showModal = (coin) => {
  elements.modalOverlay.classList.remove("hidden");
  elements.modalOverlay.setAttribute("aria-hidden", "false");
  elements.modalBody.innerHTML = `
    <div class="modal-row">
      <div class="crypto-name">
        <img src="${coin.image}" alt="${coin.name}" />
        <div>
          <strong>${coin.name}</strong>
          <p>${coin.symbol.toUpperCase()}</p>
        </div>
      </div>
      <p>${formatters.price(coin.current_price)}</p>
    </div>
    <div class="modal-stats">
      <div>
        <span>Market Cap</span>
        <strong>${formatters.marketCap(coin.market_cap)}</strong>
      </div>
      <div>
        <span>Volumen 24h</span>
        <strong>${formatters.volume(coin.total_volume)}</strong>
      </div>
      <div>
        <span>Cambio 24h</span>
        <strong class="${
          coin.price_change_percentage_24h >= 0 ? "value-positive" : "value-negative"
        }">${formatters.percent(coin.price_change_percentage_24h)}</strong>
      </div>
    </div>
  `;
};

const hideModal = () => {
  elements.modalOverlay.classList.add("hidden");
  elements.modalOverlay.setAttribute("aria-hidden", "true");
};

const updateChart = (coin, prices) => {
  elements.chartPanel.classList.remove("hidden");
  elements.chartTitle.textContent = `${coin.name} (${coin.symbol.toUpperCase()})`;
  const labels = prices.map(([timestamp]) =>
    new Date(timestamp).toLocaleDateString("es-ES", {
      weekday: "short",
      hour: "2-digit",
      minute: "2-digit",
    })
  );
  const dataPoints = prices.map(([, price]) => price);

  if (state.chart) {
    state.chart.data.labels = labels;
    state.chart.data.datasets[0].data = dataPoints;
    state.chart.update("active");
    return;
  }

  const context = elements.historyCanvas.getContext("2d");
  state.chart = new Chart(context, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: "Precio USD",
          data: dataPoints,
          borderColor: "#00d09c",
          backgroundColor: "rgba(0, 208, 156, 0.08)",
          fill: true,
          tension: 0.35,
          pointRadius: 0,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          intersect: false,
          mode: "index",
          callbacks: {
            label: (context) => formatters.price(context.parsed.y),
          },
        },
      },
      scales: {
        x: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: { color: "rgba(255,255,255,0.6)" },
        },
        y: {
          grid: { color: "rgba(255,255,255,0.05)" },
          ticks: {
            color: "rgba(255,255,255,0.6)",
            callback: (value) => `$${value}`,
          },
        },
      },
    },
  });
};

const loadCoinHistory = async (coin) => {
  const chartContent = elements.chartPanel.querySelector(".chart-content");
  const spinner = createSpinner();
  chartContent.appendChild(spinner);
  try {
    const payload = await fetchJSON(API_ROUTES.HISTORY(coin.id));
    updateChart(coin, payload.data?.prices || []);
  } catch (error) {
    elements.chartTitle.textContent = "No pudimos cargar la gráfica.";
  } finally {
    spinner.remove();
  }
};

const handleCoinSelection = (coin) => {
  state.selectedCoin = coin;
  showModal(coin);
  loadCoinHistory(coin);
};

const registerEvents = () => {
  elements.searchForm.addEventListener("submit", (event) => event.preventDefault());
  elements.searchInput.addEventListener("input", filterCryptos);
  elements.refreshButton.addEventListener("click", () => loadCryptos({ showLoader: true }));
  elements.closeModal.addEventListener("click", hideModal);
  elements.modalOverlay.addEventListener("click", (event) => {
    if (event.target === elements.modalOverlay) {
      hideModal();
    }
  });
  elements.closeChartPanel.addEventListener("click", () => {
    elements.chartPanel.classList.add("hidden");
  });
};

const startAutoRefresh = () => {
  if (state.refreshTimer) {
    clearInterval(state.refreshTimer);
  }
  state.refreshTimer = setInterval(() => loadCryptos({ showLoader: false }), REFRESH_INTERVAL_MS);
};

const init = () => {
  registerEvents();
  loadCryptos();
  startAutoRefresh();
};

document.addEventListener("DOMContentLoaded", init);
