function render() {
  const paddingLeft = 40;
  const paddingRight = 10;
  const paddingTop = 0;
  const paddingBottom = 20;

  // Minimum allowable width for the SVG - any narrower than this, and the dots become unreadable.
  const svgMinimumWidth = 800;

  const rowHeight = 20;

  const container = document.getElementById("container");

  // Use the width of the #container div if we can for the SVG, but don't let it go narrower
  // than our pre-defined minimum.
  const svgWidth = Math.max(container.getBoundingClientRect().width, svgMinimumWidth);

  // The chart area is the SVG width without the padding
  const chartWidth = svgWidth - (paddingLeft + paddingRight);

  // The SVG's height is based on the number of rows in the graphData global
  const chartHeight = rowHeight * graphData.length;
  const svgHeight = chartHeight + paddingTop + paddingBottom;

  // Compute the date extents
  const dateMin = d3.min(graphData, (channel) =>
    d3.min(channel.history, (d) => d[1])
  );

  const dateMax = d3.max(graphData, (channel) =>
    d3.max(channel.history, (d) => d[1])
  );

  const color = d3
    .scaleOrdinal()
    .domain(graphData.map((channel) => channel.name))
    .range(d3.schemeCategory10);

  const horizontal = d3
    .scaleTime()
    .domain([dateMin, dateMax])
    .range([paddingLeft, chartWidth + paddingLeft])
    .nice();

  const vertical = d3
    .scaleBand()
    .domain(graphData.map((channel) => channel.name))
    .range([chartHeight, 0]);

  const svg = d3
    .select(container)
    .selectAll("svg")
    .data([0])
    .join("svg")
    .attr("viewBox", `0 0 ${svgWidth} ${svgHeight}`)
    .attr("width", svgWidth)
    .attr("height", svgHeight);

  // Create/update graph rows
  const rowUpdate = svg.selectAll(".row").data(graphData);

  const rowEnter = rowUpdate.enter().append("g").attr("class", "row");

  const rows = rowEnter
    .merge(rowUpdate)
    .attr(
      "transform",
      (channel) => `translate(${paddingLeft} ${vertical(channel.name)})`
    )
    .attr("fill", (channel) => color(channel.name))
    .attr("stroke", (channel) => color(channel.name));

  // Create/update dots - these are clickable SVG <a> elements
  const pointUpdate = rows
    .selectAll(".row__point")
    .data((channel) => channel.history);

  const pointEnter = pointUpdate
    .enter()
    .append("a")
    .attr("class", "row__point");

  pointEnter
    .merge(pointUpdate)
    .attr(
      "transform",
      (d) => `translate(${horizontal(d[1])} ${vertical.bandwidth() * 0.25})`
    )
    .attr("href", (d) => `https://github.com/NixOS/nixpkgs/commit/${d[0]}`);

  pointEnter.append("circle").merge(pointUpdate.select("circle")).attr("r", 3);

  // Add/update hover titles
  pointEnter
    .append("title")
    .merge(pointUpdate.select("title"))
    .text(([commit, date]) => `${commit}: ${date.toLocaleString()}`);

  // Add/update row labels (channel names)
  rowEnter
    .append("text")
    .attr("class", "row__label")
    .attr("x", -paddingLeft)
    .attr("dy", "-0.1em")
    .merge(rowUpdate.select(".row__label"))
    .attr("y", vertical.bandwidth())
    .text((channel) => channel.name);

  // Add axis
  svg
    .selectAll(".axis")
    .data([0])
    .join((enter) => enter.append("g").attr("class", "axis"))
    .attr("transform", `translate(${paddingLeft} ${chartHeight})`)
    .call(d3.axisBottom(horizontal));
}

render();
window.addEventListener('resize', render);
