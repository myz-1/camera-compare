// 相机数据（与参考图一致）
const cameraData = [
    { brand: "佳能", model: "佳能5d4", avg_price: 8450.83 },
    { brand: "富士", model: "富士xs20", avg_price: 11377.83 },
    { brand: "佳能", model: "佳能80d", avg_price: 8877.00 },
    { brand: "佳能", model: "佳能r5", avg_price: 10680.50 },
    { brand: "富士", model: "富士xt4", avg_price: 5791.33 },
    { brand: "富士", model: "富士xt5", avg_price: 11880.50 },
    { brand: "尼康", model: "尼康d850", avg_price: 11063.67 },
    { brand: "尼康", model: "尼康z7ii", avg_price: 11102.17 },
    { brand: "尼康", model: "尼康z6", avg_price: 8406.67 },
    { brand: "索尼", model: "索尼a6400", avg_price: 3233.33 },
    { brand: "索尼", model: "索尼a7s3", avg_price: 13728.00 },
    { brand: "索尼", model: "索尼a7m4", avg_price: 0.00 }
];

// DOM元素
const brandBtns = document.querySelectorAll(".brand-btn");
const searchInput = document.querySelector(".search-input");
const modelSelect = document.querySelector(".model-select");
const queryBtn = document.querySelector(".query-btn");
const priceBtns = document.querySelectorAll(".price-btn");
const cameraList = document.getElementById("cameraList");

// 初始化：默认加载全部数据
window.onload = () => {
    renderCameraList(cameraData);
};

// 渲染相机列表
function renderCameraList(data) {
    cameraList.innerHTML = "";

    if (data.length === 0) {
        cameraList.innerHTML = '<div class="empty-tip">暂无相机数据，请先选择/搜索相机型号</div>';
        return;
    }

    data.forEach(item => {
        const card = document.createElement("div");
        card.className = "camera-card";
        card.innerHTML = `
            <div class="camera-name">${item.model}</div>
            <div class="camera-price">均价：${item.avg_price.toFixed(2)}元</div>
        `;
        cameraList.appendChild(card);
    });
}

// 筛选数据
function filterData(brand, search, priceRange) {
    let filtered = [...cameraData];

    // 品牌筛选
    if (brand) {
        filtered = filtered.filter(item => item.brand === brand);
    }

    // 搜索筛选
    if (search) {
        const searchStr = search.toLowerCase();
        filtered = filtered.filter(item => item.model.toLowerCase().includes(searchStr));
    }

    // 价格区间筛选
    if (priceRange) {
        const [min, max] = priceRange.split("-").map(Number);
        filtered = filtered.filter(item => item.avg_price >= min && item.avg_price <= max);
    }

    return filtered;
}

// 品牌按钮点击事件（确保响应）
brandBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        brandBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        const brand = btn.dataset.brand;
        const search = searchInput.value.trim();
        const priceRange = document.querySelector(".price-btn.active").dataset.range;
        const filtered = filterData(brand, search, priceRange);
        renderCameraList(filtered);
    });
});

// 价格按钮点击事件（确保响应）
priceBtns.forEach(btn => {
    btn.addEventListener("click", () => {
        priceBtns.forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        
        const priceRange = btn.dataset.range;
        const brand = document.querySelector(".brand-btn.active").dataset.brand;
        const search = searchInput.value.trim();
        const filtered = filterData(brand, search, priceRange);
        renderCameraList(filtered);
    });
});

// 查询按钮点击事件（确保响应）
queryBtn.addEventListener("click", () => {
    const search = searchInput.value.trim() || modelSelect.value;
    const brand = document.querySelector(".brand-btn.active").dataset.brand;
    const priceRange = document.querySelector(".price-btn.active").dataset.range;
    const filtered = filterData(brand, search, priceRange);
    renderCameraList(filtered);
    
    // 清空输入和选择
    searchInput.value = "";
    modelSelect.value = "";
});