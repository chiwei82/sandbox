const margin = { top: 20, right: 30, bottom: 240, left: 150 };
const width = 800 - margin.left - margin.right;
const height = 400 - margin.top - margin.bottom;

// 創建 SVG 容器並附加到 <div id="bar_chart">
const svg = d3.select("#bar_chart").append("svg")
    .attr("width", width + margin.left + margin.right)
    .attr("height", height + margin.top + margin.bottom)
.append("g")
    .attr("transform", `translate(${margin.left},${margin.top})`);

// 準備資料：將 "on_stop" 和 "off_stop" 組合成一個欄位
const processedData = route_data.features.map(d => ({
    stop_combination: `${d.properties.on_stop} ↔️ ${d.properties.off_stop}`,
    txn_times: d.properties.mean_of_txn_times_byRoutes
}));

// 設置 X 軸比例尺（序數類型）
const xScale = d3.scaleBand()
    .domain(processedData.map(d => d.stop_combination))
    .range([0, width])
    .padding(0.2);

// 設置 Y 軸比例尺
const yScale = d3.scaleLinear()
    .domain([0, d3.max(processedData, d => d.txn_times)])  // Y 軸範圍是 0 到最大值
    .nice()
    .range([height, 0]);

// 繪製 X 軸
svg.append("g")
    .attr("transform", `translate(0,${height})`)
    .call(d3.axisBottom(xScale))
    .selectAll("text")
    .style("text-anchor", "end")
    .attr("transform", "rotate(-45)")  // 旋轉 X 軸標籤，避免重疊
    .style("font-size", "12px");

// 繪製 Y 軸
svg.append("g")
    .call(d3.axisLeft(yScale));

svg.append("text")
    .attr("text-anchor", "middle")
    .attr("transform", "rotate(0)")  // 旋轉標題使其垂直
    .attr("x", -height / 1.705)  // 根據圖表高度垂直居中
    .attr("y", 15)  // 調整標題與 Y 軸的距離
    .style("font-size", "16px")
    .style("font-weight", "bold")
    .text("🔝前10路線");

// 繪製條形圖
svg.selectAll(".bar")
.data(processedData)
.enter().append("rect")
.attr("class", "bar")
.attr("x", d => xScale(d.stop_combination))
.attr("y", height)
.attr("width", xScale.bandwidth())
.attr("height", 0) 
.attr("fill", "steelblue")
.transition() 
.duration(800) 
.attr("y", d => yScale(d.txn_times)) 
.attr("height", d => height - yScale(d.txn_times)); 

svg.selectAll(".label")
    .data(processedData)
    .enter().append("text")
    .attr("class", "label")
    .attr("x", d => xScale(d.stop_combination) + xScale.bandwidth() / 2)
    .attr("y", height) 
    .attr("text-anchor", "middle")
    .text(d => d.txn_times)
    .style("opacity", 0)  
    .transition()
    .duration(800)  
    .attr("y", d => yScale(d.txn_times) - 5)  
    .style("opacity", 1); 