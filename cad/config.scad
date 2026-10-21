// =====================================================================
//  Ravi WR-1 welding robot - shared dimensions (mm)
//  Edit here, then run cad/build.sh to regenerate every STL.
//  Arm lengths must match config/robot.json (software).
// =====================================================================

$fn = 96;

// ---- printer tolerances: tune after printing fit_test.stl -------------
clr         = 0.20;   // radial clearance for holes, slots, shafts
bearing_fit = 0.10;   // added to bearing outer diameters (light press fit)
insert_d    = 4.2;    // hole for M3 brass heat-set insert (M3 x 5.7 type)
insert_h    = 6.0;

// ---- kinematics (same as config/robot.json) --------------------------
d1   = 210;   // shoulder axis height above the table
L2   = 160;   // shoulder -> elbow
L3   = 160;   // elbow -> wrist centre
TOOL = 90;    // wrist centre -> tool tip

// ---- bearings [bore, outer diameter, width] ----------------------------
B608  = [8, 22, 7];
B6008 = [40, 68, 15];

// ---- planetary gearmotors -- MEASURE YOUR GEARBOX AND EDIT ------------
// The output face of the gearbox bolts to a printed plate. Defaults are
// typical for NEMA17/NEMA23 planetary gearmotors but vary by vendor.
//  [ 0 face_d, 1 pilot_d, 2 pilot_h, 3 bolt_pcd, 4 bolt_d, 5 bolt_n,
//    6 bolt_angle0, 7 shaft_d, 8 flat_depth, 9 key_w, 10 key_t2,
//   11 shaft_len, 12 motor_len (face to back of motor), 13 body_sq ]
GM17_48 = [36, 22, 2.0, 28, 3, 4, 45,  8, 0.5, 0, 0,   20,  90, 42.3]; // J1, J3: NEMA17 48 mm + ~27:1
GM17_34 = [36, 22, 2.0, 28, 3, 4, 45,  8, 0.5, 0, 0,   20,  66, 42.3]; // J4, J5: NEMA17 34 mm + ~5:1
GM23_56 = [57, 40, 3.0, 50, 5, 4, 45, 14, 0,   5, 2.3, 25, 125, 57.0]; // J2: NEMA23 56 mm + 10:1

function gm_face(g)   = g[0];
function gm_pilot(g)  = g[1];
function gm_pilot_h(g)= g[2];
function gm_pcd(g)    = g[3];
function gm_bolt(g)   = g[4];
function gm_n(g)      = g[5];
function gm_a0(g)     = g[6];
function gm_shaft(g)  = g[7];
function gm_flat(g)   = g[8];
function gm_key(g)    = g[9];
function gm_key_t2(g) = g[10];
function gm_slen(g)   = g[11];
function gm_len(g)    = g[12];
function gm_sq(g)     = g[13];

// ---- base --------------------------------------------------------------
floor_t  = 5;     // floor plate
floor_r  = 100;
shell_h  = 150;   // base shell height (deck top = floor_t + shell_h)
shell_r  = 85;
wall     = 3;
deck_t   = 6;
tower_r  = 45;    // bearing tower around the two 6008 bearings
ring_t   = 8;     // spacer ring between the two 6008 outer races
ring_id  = 44;

// ---- J1 turntable -------------------------------------------------------
tt_r      = 75;
tt_t      = 10;
tt_gap    = 1;    // turntable above the deck
spigot_d  = 40;   // = 6008 bore
sh_axis_h = d1 - (floor_t + shell_h + tt_gap + tt_t);   // shoulder axis above turntable top (44)

// ---- arm widths -----------------------------------------------------------
cheek_t = 10;     // yoke cheek thickness
ua_w    = 70;     // upper arm width along the pivot axis
fa_w    = 48;     // forearm width (fits between the elbow cheeks)
sh_gap  = ua_w + 2;
el_gap  = fa_w + 2;
ua_hub_r   = 28;  // upper arm root hub radius
el_r       = 30;  // elbow cheek radius
ua_depth   = 30;  // upper arm beam depth
fa_hub_r   = 24;
fa_h       = 56;  // forearm body height
gm_recess  = 4;   // gearbox face sunk into the elbow cheek (longer shaft engagement)

// ---- forearm / wrist ----------------------------------------------------
j4_face_x  = 122; // J4 gearbox face position along the forearm
plate_t    = 6;   // gearbox mounting plates at J4 and J5
j5_face_y  = -12; // J5 gearbox face, measured from the wrist centre along the J5 axis
hub_gap    = 1;   // gap between a mounting plate and the hub it drives

// ---- tool -----------------------------------------------------------------
tool_d     = 12;  // tool shank diameter held by the tool holder (laser/pointer/pen sleeve)
