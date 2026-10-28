// Engineering baseline used by the simulation (metres, kg, N, N·m).
// Robot frame (REP 105): origin at base_footprint, on the floor under the drive-axle midpoint, +X forward, +Y left, +Z up.
// base_link is BASE_LINK_Z above it; x values equal base_link x. Heights (z) are from the floor unless a comment says "from base_link".

export const DEG = Math.PI / 180;

export const ROBOT = {
  // MMP chassis (STEP): 780 x 582, steel deck top 294 mm, 2 mm plastic top cover, 52 mm belly
  X0: -0.39, X1: 0.39, HW: 0.291, DECK: 0.294, COVER: 0.296, BELLY: 0.052,
  WHEEL_R: 0.10, WHEEL_Y: 0.20, CASTER: [[0.26, 0.215], [0.26, -0.215], [-0.29, 0.215], [-0.29, -0.215]],
  PLATE_T: 0.010, PLATE_TOP: 0.304,              // 10 mm aluminium lift base plate on the steel deck
  BP: { bp000: 0.060, bp050: 0.110 },            // column axis x from base_link: 330 mm behind the 780 mm front edge (P-03 rev19.0)
  // DOLD Hexalift V4 (BS-HM240G350530-MFF24): 240 x 60 mm basic dimension, 530 retracted, 880 extended
  COL: { L: 0.240, W: 0.060, RETRACTED: 0.530, STROKE: 0.350, HEAD: 0.012, MASS: 11.7,
         PUSH: 800, PULL: 400, SPEED: 0.018, M_LONG_STAT: 1200, M_LONG_DYN: 500, M_LAT_STAT: 450, M_LAT_DYN: 225 },
  MOUNT_ABOVE_COL: 0.166,                         // column top plate to OpenArm J1_A mount point
  MOUNT_X: 0.180,                                 // column axis to OpenArm J1_A mount point, fore-aft (option B)
  PROFILE: { X: 0.120, Y: 0.060, L: 0.340, ADAPTER: 0.010 },   // MISUMI HFS6-60120 arm profile on a 10 mm adapter plate
  MOUNT_Y: 0.031,                                 // 60 mm profile + 1 mm spacer
  STOPS: { L1000: 1.000, L1175: 1.175, L1350: 1.350 },
  BASE_LINK_Z: 0.098,                             // base_link (drive-axle midpoint) above the floor
  GEMINI: { x: 0.376, z: 0.0445 },               // base_camera_link from base_link: housing centre 142.5 mm above the floor (P-03 rev19.0)
  LIDAR_X: 0.330, LIDAR_Z: 0.222,               // RPLIDAR S3: lidar_link x from base_link; scan plane from the floor (z 0.124 from base_link)
  NEAR_Z: 0.0914, US_Y: 0.130,                   // MB7060 edge holes (y +/-0.130) and TF-Luna centre holes, 91.4 mm above the floor
  ZED_ABOVE_SH: 0.223, ZED_X: 0.222,              // ZED Mini lens: 223 mm above and 42 mm ahead of the arm mount point (x from the column axis; P-03 rev20.0, 28 Oct 2026)
};

// Totes: open plastic totes on the front deck, either side of the column (sized to the deck; not a catalogue part)
export const TOTE = { L: 0.380, W: 0.228, H: 0.200, X0: 0.000, YIN: 0.058, WALL: 0.004 };

// OpenArm 2.0 (Enactic): 4.1 kg nominal / 6.0 kg peak payload incl. end effector, 88 mm max jaw opening
export const ARMSPEC = { PAYLOAD_NOM: 4.1, PAYLOAD_PEAK: 6.0, GRIPPER_MASS_ASSUMED: 0.5, ARM_MASS: 5.5,
  JAW_MAX: 0.088, JAW_CLEAR: 0.005, REACH_SPEC: 0.606, TCP: 0.150 };

// Store: one aisle of two 3-bay gondola runs
export const STORE = {
  BAYS: 3, BAY_W: 1.0, DEPTH: 0.50, HEIGHT: 2.00, LEVELS: [0.12, 0.52, 0.92, 1.32, 1.72], SHELF_T: 0.025,
  UPRIGHT: 0.05,
};

export const CAMS = {
  head: { name: 'Head ZED Mini', hfov: 90, w: 1280, h: 720, depth: [0.10, 12], color: '#8b5cf6' },
  base: { name: 'Base Gemini 336L', hfov: 94, w: 1280, h: 800, depth: [0.17, 20], color: '#14b8a6' },
  wristL: { name: 'Left wrist', vfov: 66, w: 960, h: 600, color: '#f97316', pos: [0.023, 0.0182, -0.10236], eul: [-0.366519, 0.22689, -1.5708] },
  wristR: { name: 'Right wrist', vfov: 66, w: 960, h: 600, color: '#eab308', pos: [0.023, -0.0182, -0.10236], eul: [0.366519, 0.22689, -1.5708] },
};
