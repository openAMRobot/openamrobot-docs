// Store-page addons of three.js r160 (robot.html only). Built with 'three' mapped to window.THREE,
// the namespace of model/three-r160.min.js, so these modules add to that one three.js and carry no copy of it.
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { RectAreaLightUniformsLib } from 'three/examples/jsm/lights/RectAreaLightUniformsLib.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
Object.assign(window.THREE, { mergeGeometries, RectAreaLightUniformsLib, EffectComposer, RenderPass, GTAOPass, OutputPass });
