var map = L.map('map').setView([25.08, 121.56], 12);

L.tileLayer('https://api.mapbox.com/styles/v1/mapbox/dark-v10/tiles/{z}/{x}/{y}?access_token=pk.eyJ1Ijoic2hpYm55IiwiYSI6ImNrcWtjMDg0NjA0anQyb3RnZnl0cDJkYmYifQ.hqyJUg0ZRzAZbcJwkfs0bQ', {
    attribution: '&copy; <a href="https://www.mapbox.com/">Mapbox</a>',
}).addTo(map);

var info = L.control({position: 'bottomright'});

// map info 
info.onAdd = function (map) {
    this._div = L.DomUtil.create('div', 'info'); // create a div with a class "info"
    this.update();
    return this._div;
};

info.update = function (props) {
    this._div.innerHTML = '<h4>台北市路線交易數量 (2023年07)</h4>' +  (props ?
        '<b>' + props.name + '</b><br />' +'路線交易次數: '+ props.paths + ' 占用比率: ' + (props.paths_pct * 100).toFixed(1) +'%'
        : '移動鼠標到行政區');
};

info.addTo(map);

// 綁定按鈕點擊事件
document.getElementById("weekdayBtn").addEventListener("click", function() {
    renderMapAndBarChart("/geojson", "/top_ten_routes");
});

document.getElementById("weekendBtn").addEventListener("click", function() {
    renderMapAndBarChart("/geojson_weekend", "/top_ten_routes_weekend");
});

// 預設顯示週間資料
renderMapAndBarChart("/geojson", "/top_ten_routes");

function renderMapAndBarChart(geojsonUrl, routesUrl){
    
Promise.all([
    fetch(geojsonUrl).then(response => response.json()),  // 行政區資料
    fetch(routesUrl).then(response => response.json())  // 路線資料
])
.then(([data, route_data]) => {

    d3.select("#bar_chart").html("");
    d3.select("#line_chart").html("");

    // 清空之前的地圖圖層，只移除 L.GeoJSON 圖層
    map.eachLayer(function (layer) {
        if (layer instanceof L.GeoJSON) {
            map.removeLayer(layer);
        }
    });

    function getColor(d) {

        const pathsArray = data.features.map(feature => feature.properties.paths);
        const maxPaths = Math.max(...pathsArray);
        const minPaths = Math.min(...pathsArray);
        const ratio = (d - minPaths) / (maxPaths - minPaths);
        const hue = 30; 
        const saturation = 100;
        const lightness = 100 - ratio * 50;

        return `hsl(${hue}, ${saturation}%, ${lightness}%)`;
    }
    
    function style(feature) {
        return {
            fillColor: getColor(feature.properties.paths),
            weight: 2,
            opacity: 0.6,
            color: 'white',
            dashArray: '3',
            fillOpacity: 0.3
        };
    }
    
    L.geoJson(data, {
        style: style,
        onEachFeature: function (feature, layer) {
            layer.bindTooltip(feature.properties.name, {
                permanent: true,
                direction: 'center', 
                className: 'label-style' 
            });
        }
    }).addTo(map);

    geojson = L.geoJson(data, {
        style: style,
        onEachFeature: onEachFeature
    }).addTo(map);

    // d3
    const features = data.features;
    const names = features.map(feature => feature.properties.name);
    const paths = features.map(feature => feature.properties.paths);

    const margin = { top: 60, right: 100, bottom: 30, left:100 };
    const width = 800 - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Create the SVG element within the #line_chart div
    const svg = d3.select("#line_chart")
        .append("svg")
        .attr("width", width + margin.left + margin.right)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Set up the scales for X and Y axis
    const xScale = d3.scalePoint()
        .domain(names)  // Use the extracted names for X axis
        .range([40, width-40]);

    const yScale = d3.scaleLinear()
        .domain([d3.min(paths), d3.max(paths)])
        .nice()
        .range([height, 0]);

    // Define the line generator
    const line = d3.line()
        .x((d, i) => xScale(names[i]))
        .y(d => yScale(d))
        .curve(d3.curveMonotoneX); // Apply a smooth curve
    
    // Draw the line
    svg.append("path")
        .datum(paths)
        .attr("fill", "none")
        .attr("stroke", "steelblue")
        .attr("stroke-width", 2)
        .attr("d", line)
        .attr("stroke-dasharray", function() { return this.getTotalLength(); })
        .attr("stroke-dashoffset", function() { return this.getTotalLength(); })
        .transition()
        .duration(2000)
        .ease(d3.easeLinear)
        .attr("stroke-dashoffset", 0);
        
    // Add points at each data location
    svg.selectAll("dot")
        .data(paths)
        .enter()
        .append("circle")
        .attr("cx", (d, i) => xScale(names[i]))
        .attr("cy", d => yScale(d))
        .attr("r", 4)
        .attr("fill", "red");
    
    // Create the X axis
    svg.append("g")
        .attr("transform", `translate(0,${height})`)
        .call(d3.axisBottom(xScale))
        .selectAll("text")  // 選擇所有 X 軸的文字
        .style("font-size", "14px");;

    // Create the Y axis
    svg.append("g")
        .call(d3.axisLeft(yScale));

    const yAxis = svg.append("g")
        .call(d3.axisLeft(yScale));

    svg.selectAll("g.y-tick-line")
        .data(yScale.ticks().filter(d => d !== 0))
        .enter()
        .append("line")
        .attr("class", "y-tick-line")
        .attr("x1", 0)
        .attr("x2", width)
        .attr("y1", d => yScale(d))
        .attr("y2", d => yScale(d))
        .attr("stroke", "black")
        .attr("stroke-width", 1)
        .attr("stroke-dasharray", "4 4");

    // Create a tooltip div that is hidden by default
    const tooltip = d3.select("body").append("div")
        .style("position", "absolute")
        .style("background-color", "white")
        .style("border", "1px solid #d3d3d3")
        .style("padding", "8px")
        .style("display", "none");

    // Add hover interaction for the points
    svg.selectAll("circle")
        .on("mouseover", (event, d) => {
            tooltip.style("display", "block")
            .html(`Value: ${d}`)
            .style("left", (event.pageX + 5) + "px")
            .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => tooltip.style("display", "none"));

    //// mouseover event 連動 leaflet與 d3 js
    function highlightFeature(e) {
        var layer = e.target;
    
        layer.setStyle({
            weight: 1,
            color: '#666',
            dashArray: '',
            fillOpacity: 0.01
        });
    
        layer.bringToFront();
        info.update(layer.feature.properties);

        var featureName = layer.feature.properties.name;
        
        function highlightD3Feature(name) {
            const index = names.indexOf(name);
            if (index !== -1) {
                
                svg.selectAll("circle")
                    .filter((d, i) => names[i] === name)
                    .transition()
                    .duration(200)
                    .attr("r", (d, i) => Math.max(paths[index] / 500, 15)) 
                    .attr("fill", "orange")
                    .attr("fill-opacity", 100);
        
                svg.selectAll(".circle-text").remove();

                svg.selectAll("circle")
                    .filter((d, i) => names[i] === name) 
                    .each(function(d, i) {
                        svg.append("text")
                            .attr("class", "circle-text")
                            .attr("x", xScale(names[index]))  
                            .attr("y", yScale(paths[index]))  
                            .attr("dy", ".35em") 
                            .attr("text-anchor", "middle") 
                            .attr("font-size", Math.max(paths[index] / 1000, 15))
                            .attr("fill", "black") 
                            .text((paths[index] / 1000).toFixed(1) + "K"); 
                    });
            } else {
                console.log(`Name ${name} not found in names array`);
            }
        }
        
       // 函數：高亮 D3 條形圖
        function highlightD3Bar(districtName) {
            console.log(districtName)
            svg_bar.selectAll(".bar")
                .filter((d) => d.name === districtName)  // 將 d.name 修改為 d.district_name，這應該是匹配的正確字段
                .transition()
                .duration(200)
                .attr("fill", "orange")  // 改變顏色來表示高亮
                .attr("stroke", "black")  // 添加黑色邊框
                .attr("stroke-width", 2);  // 邊框寬度
        }
        highlightD3Feature(featureName);
        highlightD3Bar(featureName); 
    }
    
    function resetHighlight(e) {
        geojson.resetStyle(e.target);
        
        function resetD3Highlight() {
            svg.selectAll("circle")
              .transition()
              .duration(5000)
              .attr("r", 4) 
              .attr("fill", "red");
        }
        function resetD3Bar() {
            d3.selectAll(".bar")
                .transition()
                .duration(500)
                .attr("fill", "steelblue")
                .attr("stroke", "none");
        }
        resetD3Highlight();
        resetD3Bar();
        svg.selectAll(".circle-text").remove()
    }
    
    function zoomToFeature(e) {
        map.fitBounds(e.target.getBounds());
    }
    
    function onEachFeature(feature, layer) {
        layer.on({
            mouseover: highlightFeature,
            mouseout: resetHighlight,
            click: zoomToFeature
        });
        info.update();
    }
    
    //d3 bar
    const margin_bar = { top: 20, right: 30, bottom: 240, left: 150 };
    const width_bar = 800 - margin_bar.left - margin_bar.right;
    const height_bar = 400 - margin_bar.top - margin_bar.bottom;

    // 創建 SVG 容器並附加到 <div id="bar_chart">
    const svg_bar = d3.select("#bar_chart").append("svg")
        .attr("width", width_bar + margin_bar.left + margin_bar.right)
        .attr("height", height_bar + margin_bar.top + margin_bar.bottom)
        .append("g")
        .attr("transform", `translate(${margin_bar.left},${margin_bar.top})`);

    // 準備資料：將 "on_stop" 和 "off_stop" 組合成一個欄位
    const processedData = route_data.features.map(d => ({
        stop_combination: `${d.properties.on_stop} ↔️ ${d.properties.off_stop}`,
        txn_times: d.properties.mean_of_txn_times_byRoutes,
        name: d.properties.district_name
    }));

    // 設置 X 軸比例尺（序數類型）
    const xScale_bar = d3.scaleBand()
        .domain(processedData.map(d => d.stop_combination))
        .range([0, width_bar])
        .padding(0.2);

    // 設置 Y 軸比例尺
    const yScale_bar = d3.scaleLinear()
        .domain([0, d3.max(processedData, d => d.txn_times)]) 
        .nice()
        .range([height_bar, 0]);

    // 繪製 X 軸
    svg_bar.append("g")
        .attr("transform", `translate(0,${height_bar})`)
        .call(d3.axisBottom(xScale_bar))
        .selectAll("text")
        .style("text-anchor", "end")
        .attr("transform", "rotate(-45)")  
        .style("font-size", "12px");

    // 繪製 Y 軸
    svg_bar.append("g")
        .call(d3.axisLeft(yScale_bar));

    const barCount = processedData.length;
    svg_bar.append("text")
        .attr("text-anchor", "middle")
        .attr("transform", "rotate(0)")
        .attr("x", -height_bar / 1.3)  
        .attr("y", 15)
        .style("font-size", "16px")
        .style("font-weight", "bold")
        .text(`🔝前${barCount}路線`);

    // 繪製條形圖
    svg_bar.selectAll(".bar")
        .data(processedData)
        .enter().append("rect")
        .attr("class", "bar")
        .attr("x", d => xScale_bar(d.stop_combination))
        .attr("y", height_bar)
        .attr("width", xScale_bar.bandwidth())
        .attr("height", 0) 
        .attr("fill", "steelblue")
        .transition() 
        .duration(800) 
        .attr("y", d => yScale_bar(d.txn_times)) 
        .attr("height", d => height_bar - yScale_bar(d.txn_times)); 

    svg_bar.selectAll(".label")
        .data(processedData)
        .enter().append("text")
        .attr("class", "label")
        .attr("x", d => xScale_bar(d.stop_combination) + xScale_bar.bandwidth() / 2)
        .attr("y", height_bar) 
        .attr("text-anchor", "middle")
        .text(d => d.txn_times)
        .style("opacity", 0)  
        .style("font-size", "12px")
        .transition()
        .duration(800)  
        .attr("y", d => yScale_bar(d.txn_times) - 5)  
        .style("opacity", 1); 
    })

}