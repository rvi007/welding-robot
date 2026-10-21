// =====================================================================
//  Ravi WR-1 - full assembly with motors, bearings and fasteners.
//  Open in OpenSCAD and change the joint angles below (degrees, same
//  conventions as Ravi.py). F5 preview is fast; F6 render is slow.
//
//  The robot is split into links so the renderer can move each joint:
//    LINK = -1  whole robot (default)      LINK = 0..5  one link in its own frame
//    LINK =  6  work cell (table, block, T-joint coupon)
// =====================================================================

include <parts.scad>
include <vitamins.scad>

q1 = 18;     // J1 base yaw
q2 = 40;     // J2 shoulder (0 = upper arm vertical, + forward)
q3 = 12;     // J3 elbow (0 = forearm square to upper arm, + down)
q4 = 0;      // J4 forearm roll
q5 = -20;    // J5 wrist pitch (0 = tool square to forearm)

LINK       = -1;
show_scene = true;

// ---- link 0: base (fixed) -------------------------------------------------
module link0() {
    mat("printed2") base_floor();
    mat("printed2") translate([0, 0, floor_t]) base_shell(logo = false);
    mat("logo")     translate([0, 0, floor_t]) logo_base();
    mat("printed2") translate([0, 0, floor_t]) j1_motor_mount();
    translate([0, 0, tt_z + j1_face]) gearmotor_real(GM17_48);
    translate([0, 0, floor_t + shell_h - B6008[2]]) bearing(B6008);
    translate([0, 0, floor_t + tower_z]) bearing(B6008);
}

// ---- link 1: turntable + shoulder yoke (turns about Z) ---------------------
module link1() {
    translate([0, 0, tt_z]) {
        mat("printed2") { turntable(); j1_spigot(); j1_collar(); }
        mat("logo") logo_turntable();
    }
    translate([0, -sh_gap / 2 - cheek_t, tt_z + sh_az]) rotate([-90, 0, 0]) {
        gearmotor_real(GM23_56);
        mat("printed") j2_cover();
        mat("logo") logo_cover(GM23_56, 13);
    }
    translate([0, sh_gap / 2 + cheek_t, tt_z + sh_az]) rotate([90, 0, 0]) bearing(B608);
}

// ---- link 2: upper arm (origin at the shoulder axis, arm along +Z) ---------
module link2() rotate([0, -90, 0]) {
    mat("printed") { upper_arm(-1); upper_arm(1); }
    mat("logo") { logo_upper_arm(-1); logo_upper_arm(1); }
    translate([L2, -ua_w / 2 + gm_recess, 0]) rotate([-90, 0, 0]) {
        gearmotor_real(GM17_48);
        mat("printed") j3_cover();
        mat("logo") logo_cover(GM17_48, 10);
    }
    translate([L2, ua_w / 2, 0]) rotate([90, 0, 0]) bearing(B608);
    for (p = ua_bolts) {
        translate([p[0], -ua_w / 2 + 6, p[1]]) rotate([90, 0, 0]) socket_head(4);
        translate([p[0], ua_w / 2 - 5, p[1]]) rotate([-90, 0, 0]) hex_nut(4);
    }
    translate([0, sh_gap / 2 + cheek_t, 0]) rotate([-90, 0, 0]) { washer(8); translate([0, 0, 1.6]) hex_nut(8); }
}

// ---- link 3: forearm (origin at the elbow axis, forearm along +X) ----------
module link3() {
    mat("printed") { forearm(-1); forearm(1); }
    mat("logo") { logo_forearm(-1); logo_forearm(1); }
    translate([j4_face_x, 0, 0]) rotate([0, 90, 0]) gearmotor_real(GM17_34);
    for (p = fa_bolts) {
        translate([p[0], -fa_w / 2 + 3.5, p[1]]) rotate([90, 0, 0]) socket_head(3);
        translate([p[0], fa_w / 2 - 3, p[1]]) rotate([-90, 0, 0]) hex_nut(3);
    }
    translate([0, ua_w / 2, 0]) rotate([-90, 0, 0]) { washer(8); translate([0, 0, 1.6]) hex_nut(8); }
}

// ---- link 4: wrist (origin at the wrist centre, X = forearm axis) ----------
module link4() {
    mat("printed") wrist();
    translate([0, j5_face_y, 0]) rotate([-90, 0, 0]) gearmotor_real(GM17_34);
}

// ---- link 5: tool holder + pointer (origin at the wrist centre) ------------
module link5() {
    mat("printed2") tool_holder();
    pointer();
}

module robot(q1, q2, q3, q4, q5) {
    link0();
    rotate([0, 0, q1]) {
        link1();
        translate([0, 0, d1]) rotate([0, q2, 0]) {
            link2();
            translate([0, 0, L2]) rotate([0, q3, 0]) {
                link3();
                translate([L3, 0, 0]) rotate([q4, 0, 0]) {
                    link4();
                    rotate([0, q5, 0]) link5();
                }
            }
        }
    }
}

if (LINK < 0) {
    robot(q1, q2, q3, q4, q5);
    if (show_scene) work_scene();
}
else if (LINK == 0) link0();
else if (LINK == 1) link1();
else if (LINK == 2) link2();
else if (LINK == 3) link3();
else if (LINK == 4) link4();
else if (LINK == 5) link5();
else if (LINK == 6) work_scene();
