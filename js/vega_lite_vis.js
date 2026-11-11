/* Embeds every Vega-Lite visualisation into its container div.
   One vg_N variable + one vegaEmbed call per chart, per the unit's convention.
   Chart failures are shown inside the card instead of failing silently. */
var vg_1 = "act2_star_heatmap.vg.json";
var vg_2 = "act2b_repeat_dumbbell.vg.json";
var vg_3 = "act2d_network_slope.vg.json";
var vg_4 = "act2c_network_reigns.vg.json";
var vg_5 = "act3_aacta_network.vg.json";
var vg_6 = "act3b_genre_compare.vg.json";
var vg_7 = "act3c_canon_matrix.vg.json";
var vg_8 = "act3d_gender.vg.json";
var vg_9 = "act4a_map_birthplaces.vg.json";
var vg_10 = "act4b_map_choropleth.vg.json";
var vg_11 = "act4c_map_symbols.vg.json";

var charts = [
  [vg_1, "#vis-act2-star-heatmap"],
  [vg_2, "#vis-act2-repeat-dumbbell"],
  [vg_3, "#vis-act2-network-slope"],
  [vg_4, "#vis-act2-network-reigns"],
  [vg_5, "#vis-act3-aacta-network"],
  [vg_6, "#vis-act3-genre-compare"],
  [vg_7, "#vis-act3-canon-matrix"],
  [vg_8, "#vis-act3-gender"],
  [vg_9, "#vis-act4-map-birthplaces"],
  [vg_10, "#vis-act4-map-choropleth"],
  [vg_11, "#vis-act4-map-symbols"]
];

charts.forEach(function (c) {
  vegaEmbed(c[1], c[0]).then(function (result) {
    // access the vega view instance via result.view if needed
  }).catch(function (err) {
    console.error(c[0], err);
    var box = document.createElement("p");
    box.className = "chart-error";
    box.textContent = "Chart failed to load: " + c[0] + " - " + err.message +
      " (check that this file exists and its data files are present in data/)";
    document.querySelector(c[1]).appendChild(box);
  });
});
