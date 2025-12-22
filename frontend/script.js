// ===================== 核心配置 =====================
// 图片加载失败兜底函数
function handleImgError(imgElement) {
    imgElement.src = "./img/default.jpg"; // 默认图（必须放在frontend/img下）
    imgElement.alt = "相机默认图片";
    imgElement.style.objectFit = "cover";
}

// 型号默认描述（补充后端可能缺失的简介）
const MODEL_DESC = {
    // 佳能
    "佳能80D": "佳能80D是一款中端单反相机，搭载2420万像素APS-C画幅CMOS传感器，DIGIC 6图像处理器，支持全像素双核AF，连拍速度7张/秒，翻转触摸屏设计。",
    "佳能R100": "佳能R100入门级微单，轻量化机身，2410万像素APS-C传感器，操作简单，性价比极高，适合摄影新手。",
    "佳能R50": "佳能R50便携微单，2420万像素，翻转触摸屏，支持4K视频，适合日常拍摄和vlog创作。",
    "佳能R7": "佳能R7中端微单，3250万像素APS-C传感器，15张/秒连拍，对焦性能出色，适合运动摄影。",
    "佳能R6": "佳能R6全画幅微单，2010万像素，8级机身防抖，4K 60p视频，专业级综合性能。",
    "佳能5D4": "佳能5D4全画幅专业单反，3040万像素，DIGIC 6+处理器，高感表现优秀，适合商业摄影。",
    "佳能6D2": "佳能6D2入门全画幅单反，2620万像素，翻转屏，内置Wi-Fi，轻量化易上手。",
    "佳能R8": "佳能R8轻量化全画幅微单，2420万像素，小巧便携，兼顾画质与便携性。",
    "佳能R10": "佳能R10入门微单，2420万像素，14张/秒连拍，适合新手和vlogger。",
    "佳能M50 II": "佳能M50 II便携微单，2410万像素，翻转触摸屏，复古外观，视频性能升级。",
    "佳能R5": "佳能R5旗舰全画幅微单，4500万像素，8K视频录制，机身防抖，专业级天花板。",
    "佳能850D": "佳能850D入门单反，2410万像素，4K视频，翻转触摸屏，性价比高。",
    // 尼康
    "尼康Z6": "尼康Z6全画幅微单，2450万像素，EXPEED 6处理器，高感优秀，视频拍照兼顾。",
    "尼康D850": "尼康D850全画幅专业单反，4575万像素，8K延时，高分辨率，适合风光摄影。",
    "尼康Z7II": "尼康Z7II全画幅微单，4575万像素，双卡槽，对焦和续航升级，高像素首选。",
    "尼康Z5": "尼康Z5入门全画幅微单，2432万像素，五轴防抖，性价比高的全画幅入门之选。",
    "尼康Z8": "尼康Z8旗舰微单，4575万像素，8K视频，旗舰级性能，轻量化设计。",
    "尼康D7500": "尼康D7500中端单反，2088万像素，EXPEED 5处理器，51点AF，4K视频。",
    "尼康D5600": "尼康D5600入门单反，2416万像素，翻转触摸屏，操作简单，适合新手。",
    "尼康Zfc": "尼康Zfc复古微单，2088万像素，APS-C画幅，经典胶片模拟，颜值出众。",
    "尼康Z9": "尼康Z9顶级旗舰微单，4575万像素，8K 60p视频，无机械快门，专业体育摄影首选。",
    // 索尼
    "索尼A7M4": "索尼A7M4全画幅微单，3300万像素，AI智能对焦，8K 24p视频，性价比旗舰。",
    "索尼A6400": "索尼A6400 APS-C微单，2420万像素，实时眼部对焦，180°翻转屏，vlog神器。",
    "索尼A7S3": "索尼A7S3全画幅视频微单，1210万像素，4K 120p视频，专业视频创作者首选。",
    "索尼A7C": "索尼A7C轻量化全画幅微单，2420万像素，小巧便携，兼顾画质与便携。",
    "索尼A7R5": "索尼A7R5高像素旗舰，6100万像素，8K视频，AI对焦，高分辨率摄影首选。",
    "索尼ZV-E10": "索尼ZV-E10视频入门微单，2420万像素，翻转屏，专门优化vlog拍摄。",
    "索尼A6700": "索尼A6700中端APS-C微单，2600万像素，4K 60p视频，对焦性能拉满。",
    "索尼FX3": "索尼FX3专业视频机，全画幅，4K 120p视频，电影级画质，适合专业创作。",
    "索尼A1": "索尼A1顶级全画幅旗舰，5010万像素，30张/秒连拍，8K视频，性能天花板。",
    // 富士
    "富士Xt5": "富士XT5复古微单，4020万像素APS-C传感器，五轴防抖，30种胶片模拟，文艺首选。",
    "富士Xs20": "富士XS20 APS-C无反相机，2610万像素，五轴防抖，8K视频，复古外观+高性能。",
    "富士Xt4": "富士XT4复古微单，2610万像素，五轴防抖，胶片模拟，视频拍照双优。",
    "富士XT30II": "富士XT30 II入门复古微单，2610万像素，轻量化，胶片模拟丰富，易上手。",
    "富士X100V": "富士X100V复古旁轴，2610万像素，固定镜头，胶片模拟，街拍神器。",
    "富士XS10": "富士XS10中端APS-C微单，2610万像素，五轴防抖，翻转屏，性价比高。",
    "富士GFX50SII": "富士GFX 50S II中画幅相机，5140万像素，中画幅画质，轻量化设计。",
    "富士X-H2": "富士X-H2旗舰APS-C微单，4020万像素，8K视频，高分辨率+高速连拍。"

};

// ===================== DOM元素 =====================
const jdGoodsList = document.querySelector('.jd-goods-list');
const brandBtns = document.querySelectorAll('.filter-btn[data-brand]');
const modelSelect = document.querySelector('.model-select');
const searchInput = document.querySelector('.jd-search-input');
const searchBtn = document.querySelector('.jd-search-btn');
const detailModal = document.getElementById('detailModal');
const modalClose = document.querySelector('.modal-close');
const modalCloseBtn = document.querySelector('.modal-close-btn');

// 存储从后端拉取的全量数据
let allCameraData = [];

// ===================== 页面初始化 =====================
window.onload = async () => {
    // 1. 优先从后端拉取所有型号数据（核心！不再用前端硬编码）
    await loadDataFromBackend();
    // 2. 初始化型号下拉框（基于后端返回的全量数据）
    initModelSelect();
    // 3. 渲染所有商品（后端的全量型号）
    renderGoodsList(allCameraData);
};

// ===================== 核心：从后端拉取全量数据 =====================
async function loadDataFromBackend() {
    try {
        // 请求后端接口（替换为你的后端地址，保持一致）
        const response = await fetch('http://127.0.0.1:5000/api/camera/all');
        const result = await response.json();

        if (result.code === 0 && result.data.length > 0) {
            // 对后端返回的每个型号做标准化处理（补全图片/价格/简介）
            allCameraData = result.data.map(item => {
                // 统一型号命名（小写转大写、去空格）
                const standardModel = item.camera_model.replace(/\s+/g, '').replace(/d/g, 'D').replace(/z/g, 'Z').replace(/x/g, 'X');
                // 自动生成本地图片路径（规则：./img/标准化型号.jpg）
                const imgPath = `./img/${standardModel}.jpg`;
                // 补全价格（后端只有min/max的话，生成3个中间价格）
                const jdPrices = item.jd_prices || generatePriceList(item.min_price, item.max_price, 3);
                const xianyuPrices = item.xianyu_prices || generatePriceList(Math.floor(item.min_price*0.7), Math.floor(item.max_price*0.8), 3);
                // 补全简介
                const desc = item.desc || MODEL_DESC[standardModel] || "暂无产品简介";
                // 计算参考均价
                const refAvg = (jdPrices.reduce((a,b)=>a+b,0)/jdPrices.length + xianyuPrices.reduce((a,b)=>a+b,0)/xianyuPrices.length)/2;

                return {
                    brand: item.brand,
                    camera_model: standardModel,
                    img: imgPath,
                    desc: desc,
                    jd_prices: jdPrices,
                    xianyu_prices: xianyuPrices,
                    ref_avg: refAvg,
                    min_price: item.min_price,
                    max_price: item.max_price
                };
            });
            console.log("✅ 从后端拉取到全量数据：", allCameraData);
        } else {
            // 后端无数据时，用你提供的全量型号生成默认数据（兜底）
            console.log("⚠️ 后端无数据，使用默认全量型号");
            allCameraData = generateDefaultFullData();
        }
    } catch (error) {
        // 接口请求失败时，用默认全量型号兜底
        console.error("❌ 后端接口请求失败：", error);
        allCameraData = generateDefaultFullData();
    }
}

// 辅助：生成价格列表（从min到max均分3个价格）
function generatePriceList(min, max, count) {
    const step = Math.floor((max - min) / (count - 1));
    return Array.from({length: count}, (_, i) => min + i * step);
}

// 辅助：生成你提供的全量型号默认数据（后端无数据时兜底）
function generateDefaultFullData() {
    const defaultData = [];
    // 佳能
    const canonModels = [
        {"model": "佳能80D", "min_price": 1000, "max_price": 20000},
        {"model": "佳能R100", "min_price": 500, "max_price": 10000},
        {"model": "佳能R50", "min_price": 2000, "max_price": 10000},
        {"model": "佳能R7", "min_price": 1000, "max_price": 20000},
        {"model": "佳能R6", "min_price": 1000, "max_price": 20000},
        {"model": "佳能5D4", "min_price": 3000, "max_price": 25000},
        {"model": "佳能6D2", "min_price": 2000, "max_price": 18000},
        {"model": "佳能R8", "min_price": 4000, "max_price": 15000},
        {"model": "佳能R10", "min_price": 1500, "max_price": 12000},
        {"model": "佳能M50 II", "min_price": 1000, "max_price": 8000},
        {"model": "佳能R5", "min_price": 8000, "max_price": 35000},
        {"model": "佳能850D", "min_price": 1500, "max_price": 9000}
    ];
    // 尼康
    const nikonModels = [
        {"model": "尼康Z6", "min_price": 2000, "max_price": 30000},
        {"model": "尼康D850", "min_price": 4000, "max_price": 28000},
        {"model": "尼康Z7II", "min_price": 6000, "max_price": 35000},
        {"model": "尼康Z5", "min_price": 3000, "max_price": 18000},
        {"model": "尼康Z8", "min_price": 15000, "max_price": 45000},
        {"model": "尼康D7500", "min_price": 1500, "max_price": 10000},
        {"model": "尼康D5600", "min_price": 1000, "max_price": 8000},
        {"model": "尼康Zfc", "min_price": 2000, "max_price": 10000},
        {"model": "尼康Z9", "min_price": 10000, "max_price": 60000}
    ];
    // 索尼
    const sonyModels = [
        {"model": "索尼A7M4", "min_price": 5000, "max_price": 15000},
        {"model": "索尼A6400", "min_price": 2000, "max_price": 8000},
        {"model": "索尼A7S3", "min_price": 10000, "max_price": 40000},
        {"model": "索尼A7C", "min_price": 4000, "max_price": 16000},
        {"model": "索尼A7R5", "min_price": 12000, "max_price": 38000},
        {"model": "索尼ZV-E10", "min_price": 2000, "max_price": 8000},
        {"model": "索尼A6700", "min_price": 3000, "max_price": 10000},
        {"model": "索尼FX3", "min_price": 15000, "max_price": 40000},
        {"model": "索尼A1", "min_price": 10000, "max_price": 60000}
    ];
    // 富士
    const fujifilmModels = [
        {"model": "富士XT5", "min_price": 4000, "max_price": 12000},
        {"model": "富士XS20", "min_price": 3000, "max_price": 10000},
        {"model": "富士XT4", "min_price": 3500, "max_price": 11000},
        {"model": "富士XT30 II", "min_price": 2500, "max_price": 9000},
        {"model": "富士X100V", "min_price": 4000, "max_price": 12000},
        {"model": "富士XS10", "min_price": 3000, "max_price": 10000},
        {"model": "富士GFX 50S II", "min_price": 10000, "max_price": 35000},
        {"model": "富士X-H2", "min_price": 6000, "max_price": 18000}
    ];

    // 整合所有品牌
    const allBrandModels = [
        {brand: "佳能", models: canonModels},
        {brand: "尼康", models: nikonModels},
        {brand: "索尼", models: sonyModels},
        {brand: "富士", models: fujifilmModels}
    ];

    // 生成每个型号的完整数据
    allBrandModels.forEach(({brand, models}) => {
        models.forEach(item => {
            const standardModel = item.model.replace(/\s+/g, '').replace(/d/g, 'D').replace(/z/g, 'Z').replace(/x/g, 'X');
            const jdPrices = generatePriceList(item.min_price, item.max_price, 3);
            const xianyuPrices = generatePriceList(Math.floor(item.min_price*0.7), Math.floor(item.max_price*0.8), 3);
            const refAvg = (jdPrices.reduce((a,b)=>a+b,0)/jdPrices.length + xianyuPrices.reduce((a,b)=>a+b,0)/xianyuPrices.length)/2;
            
            defaultData.push({
                brand: brand,
                camera_model: standardModel,
                img: `./img/${standardModel}.jpg`,
                desc: MODEL_DESC[standardModel] || "暂无产品简介",
                jd_prices: jdPrices,
                xianyu_prices: xianyuPrices,
                ref_avg: refAvg,
                min_price: item.min_price,
                max_price: item.max_price
            });
        });
    });

    return defaultData;
}

// ===================== 页面交互逻辑 =====================
// 初始化型号下拉框（基于后端全量数据）
function initModelSelect() {
    const modelMap = {};
    allCameraData.forEach(item => {
        const brand = item.brand;
        const model = item.camera_model;
        if (!modelMap[brand]) modelMap[brand] = [];
        if (!modelMap[brand].includes(model)) {
            modelMap[brand].push(model);
        }
    });

    let options = '<option value="">全部型号</option>';
    for (const brand in modelMap) {
        options += `<optgroup label="${brand}">`;
        modelMap[brand].forEach(model => {
            options += `<option value="${model}">${model}</option>`;
        });
        options += `</optgroup>`;
    }
    modelSelect.innerHTML = options;
}

// 渲染全量商品列表
function renderGoodsList(data) {
    jdGoodsList.innerHTML = '';

    if (!data || data.length === 0) {
        jdGoodsList.innerHTML = `
            <div class="empty-state">
                <i class="iconfont icon-empty"></i>
                <p>暂无符合条件的相机数据</p>
            </div>
        `;
        return;
    }

    data.forEach(item => {
        // 计算均价
        const jdAvg = (item.jd_prices.reduce((a, b) => a + b, 0) / item.jd_prices.length).toFixed(0);
        const xyAvg = (item.xianyu_prices.reduce((a, b) => a + b, 0) / item.xianyu_prices.length).toFixed(0);

        // 创建商品卡片
        const card = document.createElement('div');
        card.className = 'goods-card';
        card.dataset.model = item.camera_model;
        card.innerHTML = `
            <img src="${item.img}" alt="${item.camera_model}" class="card-img" onerror="handleImgError(this)" style="object-fit: cover; height: 180px;">
            <div class="card-info">
                <h3 class="card-model">${item.camera_model}</h3>
                <p class="card-brand">${item.brand}</p>
                <div class="card-price">
                    <span class="card-price-tag">¥${jdAvg}</span>
                    <span class="card-price-avg">/ 闲鱼¥${xyAvg}</span>
                </div>
            </div>
        `;

        // 卡片点击打开详情弹窗
        card.addEventListener('click', () => {
            openDetailModal(item);
        });

        jdGoodsList.appendChild(card);
    });
}

// 打开详情弹窗
function openDetailModal(item) {
    // 填充图片
    const detailImg = document.getElementById('detailImg');
    detailImg.src = item.img;
    detailImg.alt = item.camera_model;
    detailImg.onerror = () => handleImgError(detailImg);
    detailImg.style.objectFit = "cover";

    // 填充基础信息
    document.getElementById('detailModel').textContent = item.camera_model;
    document.getElementById('detailBrand').textContent = `品牌：${item.brand}`;
    document.getElementById('detailDesc').textContent = item.desc;

    // 填充京东价格
    const jdPrices = document.getElementById('jdPrices');
    jdPrices.innerHTML = '';
    item.jd_prices.forEach(price => {
        const tag = document.createElement('span');
        tag.className = 'price-tag';
        tag.textContent = `¥${price}`;
        jdPrices.appendChild(tag);
    });
    const jdAvg = (item.jd_prices.reduce((a,b)=>a+b,0)/item.jd_prices.length).toFixed(0);
    document.getElementById('jdAvg').textContent = `¥${jdAvg}`;

    // 填充闲鱼价格
    const xyPrices = document.getElementById('xyPrices');
    xyPrices.innerHTML = '';
    item.xianyu_prices.forEach(price => {
        const tag = document.createElement('span');
        tag.className = 'price-tag';
        tag.textContent = `¥${price}`;
        xyPrices.appendChild(tag);
    });
    const xyAvg = (item.xianyu_prices.reduce((a,b)=>a+b,0)/item.xianyu_prices.length).toFixed(0);
    document.getElementById('xyAvg').textContent = `¥${xyAvg}`;

    // 显示弹窗
    detailModal.style.display = 'block';
}

// 关闭弹窗
function closeModal() {
    detailModal.style.display = 'none';
}
modalClose.addEventListener('click', closeModal);
modalCloseBtn.addEventListener('click', closeModal);
document.querySelector('.modal-mask').addEventListener('click', closeModal);
document.querySelector('.modal-content').addEventListener('click', (e) => e.stopPropagation());

// 筛选逻辑（支持品牌/型号/搜索）
function filterGoods(brand = '', model = '', search = '') {
    let filtered = [...allCameraData];
    // 品牌筛选
    if (brand) filtered = filtered.filter(item => item.brand === brand);
    // 型号筛选
    if (model) filtered = filtered.filter(item => item.camera_model === model);
    // 搜索筛选（关键词匹配）
    if (search) {
        const keyword = search.toLowerCase();
        filtered = filtered.filter(item => 
            item.camera_model.toLowerCase().includes(keyword) || 
            item.brand.toLowerCase().includes(keyword)
        );
    }
    return filtered;
}

// 品牌筛选事件
brandBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        brandBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        const filtered = filterGoods(btn.dataset.brand, modelSelect.value, searchInput.value.trim());
        renderGoodsList(filtered);
    });
});

// 型号筛选事件
modelSelect.addEventListener('change', () => {
    const activeBrand = document.querySelector('.filter-btn.active').dataset.brand;
    const filtered = filterGoods(activeBrand, modelSelect.value, searchInput.value.trim());
    renderGoodsList(filtered);
});

// 搜索事件
searchBtn.addEventListener('click', () => {
    const activeBrand = document.querySelector('.filter-btn.active').dataset.brand;
    const filtered = filterGoods(activeBrand, modelSelect.value, searchInput.value.trim());
    renderGoodsList(filtered);
});
searchInput.addEventListener('keydown', (e) => e.key === 'Enter' && searchBtn.click());