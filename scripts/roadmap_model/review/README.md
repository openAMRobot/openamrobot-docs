# Review renders

Labelled engineering renders of the roadmap model for design review: every part and cable in a view gets a numbered marker, and a legend on the right gives the component name (from the model registry) or the cable ID, function, harness, gauge and length (from model/cable_list.csv). Blocked cables are red.

```
(cd docs/assets/roadmap && python3 -m http.server 8765) &
node scripts/roadmap_model/review/review_shots.js scripts/roadmap_model/review/views.json evidence/<folder> [name filter]
```

views.json: one entry per picture with name, title, sub, target [x, y, z] (base_footprint, m), az and el (deg), dist (m) with fov, or ortho (view height in m), lift (travel in m), hide, ghost or ghostAll with keep (part ids, trailing * as a wildcard), hideUpper (1 moving stage, 2 whole lift), labels (part ids) and cables (cable ids).
