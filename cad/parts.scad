// =====================================================================
//  Ravi WR-1 welding robot - printable parts
//  Every part is modelled in its assembly frame; print_<part>() turns it
//  into the orientation it should be printed in (flat face on the bed).
// =====================================================================

include <config.scad>

eps = 0.01;

// ---------------------------------------------------------------------
//  helpers
// ---------------------------------------------------------------------

// Hole along +Z from z=0. td = teardrop tip angle in the XY plane (deg) for
// holes that print sideways; leave undef for a round hole.
module hole(d, h, td = undef) {
    if (is_undef(td)) cylinder(d = d, h = h);
    else linear_extrude(h) rotate(td - 90) union() { circle(d = d); rotate(45) square(d / 2); }
}

// Gearmotor output shaft: D-flat (flat towards +Y) or keyed (key towards +Y).
module shaft_profile(g) {
    r = (gm_shaft(g) + clr) / 2;
    if (gm_key(g) > 0) {
        circle(r = r);
        translate([-(gm_key(g) + clr) / 2, 0])
            square([gm_key(g) + clr, gm_shaft(g) / 2 + gm_key_t2(g) + clr / 2]);
    } else {
        intersection() {
            circle(r = r);
            translate([-r, -r]) square([2 * r, r + gm_shaft(g) / 2 - gm_flat(g) + clr / 2]);
        }
    }
}
module shaft_bore(g, h) linear_extrude(h) shaft_profile(g);

// Cut for a gearbox bolted to a plate lying in z = [0, t].
// Gearbox face against z = 0, shaft pointing +Z, button-head screws from z = t.
module gm_mount_cut(g, t, recess = 0, td = undef) {
    translate([0, 0, -eps]) {
        hole(gm_pilot(g) + 2 * clr, t + 2 * eps, td);
        for (i = [0 : gm_n(g) - 1])
            rotate(gm_a0(g) + i * 360 / gm_n(g)) translate([gm_pcd(g) / 2, 0, 0]) {
                hole(gm_bolt(g) + clr, t + 2 * eps, td);
                hd = gm_bolt(g) * 0.6 + 0.4;                       // button head height
                translate([0, 0, t - hd + eps]) hole(gm_bolt(g) * 1.9 + 0.6, hd + eps, td);
            }
        if (recess > 0) hole(gm_face(g) + 2 * clr, recess + eps, td);
    }
}

// M3 nut trap with a set screw hole, screw along +Z starting at z = 0.
module setscrew_m3(len, nut_at) {
    translate([0, 0, -eps]) cylinder(d = 3.3, h = len + eps);
    translate([0, 0, nut_at]) hull() {
        cylinder(d = 6.4, h = 2.6, $fn = 6);
        translate([0, 20, 0]) cylinder(d = 6.4, h = 2.6, $fn = 6);
    }
}

// Simple stand-in for a gearmotor (assembly preview only). Face at z = 0, shaft +Z.
module gearmotor(g) {
    color("#9aa3ad") {
        translate([0, 0, -min(35, gm_len(g) / 2)])
            if (gm_face(g) > 50) translate([-gm_face(g) / 2, -gm_face(g) / 2, 0])
                cube([gm_face(g), gm_face(g), min(35, gm_len(g) / 2)]);
            else cylinder(d = gm_face(g), h = min(35, gm_len(g) / 2));
        translate([-gm_sq(g) / 2, -gm_sq(g) / 2, -gm_len(g)])
            cube([gm_sq(g), gm_sq(g), gm_len(g) - min(35, gm_len(g) / 2)]);
    }
    color("#d0d0d0") cylinder(d = gm_shaft(g), h = gm_slen(g));
}

// ---------------------------------------------------------------------
//  derived positions
// ---------------------------------------------------------------------
tower_z   = shell_h - (2 * B6008[2] + ring_t);     // bottom of the bearing tower (shell frame)
tt_z      = floor_t + shell_h + tt_gap;             // turntable underside (world)
stack_bot = -(tt_gap + 2 * B6008[2] + ring_t);      // bottom of bearing stack (turntable frame) = -39
spigot_l  = -stack_bot - 0.5;                       // 0.5 short so the collar preloads the bearings
collar_h  = 12;
j1_face   = stack_bot - 0.5 - gm_slen(GM17_48);     // J1 gearbox face (turntable frame)
j1_plate  = 7;
sh_az     = tt_t + sh_axis_h;                       // shoulder axis above turntable underside
bolt_r    = 15;                                     // spigot / collar bolt circle radius

// ---------------------------------------------------------------------
//  base
// ---------------------------------------------------------------------
module base_floor() {
    difference() {
        cylinder(r = floor_r, h = floor_t);
        translate([0, 0, -eps]) linear_extrude(floor_t + 2 * eps) square(46, center = true);
        for (a = [45 : 90 : 315]) rotate(a) translate([0, 0, -eps])        // clamp / bolt-down slots
            linear_extrude(floor_t + 2 * eps) hull() {
                translate([floor_r - 7, 0]) circle(d = 6.6);
                translate([floor_r + 5, 0]) circle(d = 6.6);
            }
        for (a = [0 : 60 : 300]) rotate(a) translate([shell_r - 7, 0, -eps]) {   // countersunk M3
            cylinder(d = 3.4, h = floor_t + 2 * eps);
            cylinder(d1 = 6.6, d2 = 3.4, h = 1.8);
        }
        rotate(180) translate([shell_r - 6, -9, -eps]) cube([40, 18, floor_t + 2 * eps]);  // cable notch
    }
}

module base_shell() {
    difference() {
        union() {
            difference() {
                cylinder(r = shell_r, h = shell_h);
                translate([0, 0, -eps]) cylinder(r = shell_r - wall, h = shell_h - deck_t + eps);
            }
            translate([0, 0, tower_z]) cylinder(r = tower_r, h = shell_h - tower_z);
            for (a = [0 : 60 : 300]) rotate(a)
                translate([tower_r - 2, -2, tower_z]) cube([shell_r - wall - tower_r + 4, 4, shell_h - tower_z]);
            for (a = [0 : 60 : 300]) rotate(a) translate([shell_r - 7, 0, 0]) cylinder(r = 5.5, h = 12);
        }
        // 6008 seats with the spacer ring between them
        translate([0, 0, shell_h - B6008[2]]) cylinder(d = B6008[1] + bearing_fit, h = B6008[2] + eps);
        translate([0, 0, tower_z - eps]) cylinder(d = B6008[1] + bearing_fit, h = B6008[2] + eps);
        translate([0, 0, tower_z - eps]) cylinder(d = ring_id, h = shell_h - tower_z + 2 * eps);
        for (a = [30, 150, 270]) rotate(a) translate([40, 0, tower_z - eps]) cylinder(d = insert_d, h = insert_h + 1);
        for (a = [0 : 60 : 300]) rotate(a) translate([shell_r - 7, 0, -eps]) cylinder(d = insert_d, h = insert_h + 1);
        rotate(180) translate([0, 0, 22]) rotate([0, 90, 0]) cylinder(d = 16, h = shell_r + 5);   // cables
        for (dy = [-6, 6]) rotate(30) translate([80, dy, shell_h - insert_h])                    // J1 switch
            cylinder(d = insert_d, h = insert_h + eps);
    }
}

// J1 gearmotor carrier: bolts under the bearing tower.
module j1_motor_mount() {
    zf = tt_z - floor_t + j1_face;            // gearbox face in the shell frame
    zt = tower_z;
    difference() {
        rotate_extrude() polygon([
            [26, zf], [30, zf], [30, zt - 19], [tower_r, zt - 4], [tower_r, zt], [26, zt]]);
        for (a = [30, 150, 270]) rotate(a) translate([40, 0, 0]) {
            translate([0, 0, zt - 4 - eps]) cylinder(d = 3.4, h = 4 + 2 * eps);
            translate([0, 0, zf - eps]) cylinder(d = 6.5, h = zt - 4 - zf + eps);
        }
        for (a = [0, 180]) rotate(a) translate([20, -9, zf + j1_plate + 0.6]) cube([20, 18, zt - zf - j1_plate - 5]);
    }
    difference() {
        translate([0, 0, zf]) cylinder(r = 30, h = j1_plate);
        translate([0, 0, zf]) gm_mount_cut(GM17_48, j1_plate);
    }
}

// Tube through the two 6008 bearings, bolted under the turntable.
module j1_spigot() {
    difference() {
        union() {
            translate([0, 0, -spigot_l]) cylinder(d = spigot_d - 0.1, h = spigot_l);
            translate([0, 0, -tt_gap]) cylinder(d = 45, h = tt_gap);          // presses the upper inner race
        }
        for (a = [30, 150, 270]) rotate(a) translate([bolt_r, 0, -spigot_l - eps]) cylinder(d = 3.4, h = spigot_l + 1);
        translate([0, 0, -spigot_l - eps]) cylinder(d = 14, h = spigot_l + 1);
    }
}

// Couples the J1 shaft to the spigot and preloads the bearing pair.
module j1_collar() {
    z0 = stack_bot - collar_h;
    difference() {
        translate([0, 0, z0]) cylinder(d = 45, h = collar_h);
        translate([0, 0, z0 - eps]) shaft_bore(GM17_48, collar_h + 2 * eps);
        for (a = [30, 150, 270]) rotate(a) translate([bolt_r, 0, z0 - eps]) {
            cylinder(d = 3.4, h = collar_h + 1);
            cylinder(d = 6.2, h = 8.5);                   // M3 x 50 heads sit deep
        }
        translate([0, 0, z0 + collar_h / 2]) rotate([-90, 0, 0]) rotate([0, 0, 0])
            setscrew_m3(25, 7);
    }
}

// ---------------------------------------------------------------------
//  turntable + shoulder yoke (J1 output, carries J2)
// ---------------------------------------------------------------------
module cheek(t, az, r) {
    hull() {
        translate([-r, 0, 0]) cube([2 * r, t, 1]);
        translate([0, 0, az]) rotate([-90, 0, 0]) cylinder(r = r, h = t);
    }
}

module turntable() {
    yi = sh_gap / 2;
    yo = yi + cheek_t;
    cr = 32;
    difference() {
        union() {
            cylinder(r = tt_r, h = tt_t);
            translate([0, -yo, 0]) cheek(cheek_t, sh_az, cr);
            translate([0, yi, 0]) cheek(cheek_t, sh_az, cr);
            for (s = [-1, 1], x = [-cr - 1, cr - 3]) translate([x, 0, 0])      // outer gussets
                hull() {
                    translate([0, s * yo, tt_t - 1]) cube([4, eps, 32]);
                    translate([0, s * (yo + 20), tt_t - 1]) cube([4, eps, 1]);
                }
            rotate(180) translate([tt_r - 6, -4, 0]) cube([11, 8, tt_t]);       // J1 homing dog
        }
        translate([0, -yo, sh_az]) rotate([-90, 0, 0]) gm_mount_cut(GM23_56, cheek_t, td = 270);
        translate([0, yo, sh_az]) rotate([90, 0, 0]) {
            translate([0, 0, -eps]) hole(B608[1] + bearing_fit, B608[2] + eps, 90);
            hole(12.5, cheek_t + 2 * eps, 90);
        }
        for (a = [30, 150, 270]) rotate(a) translate([bolt_r, 0, -eps]) cylinder(d = insert_d, h = insert_h + 2);
        translate([0, 0, -eps]) cylinder(d = 14, h = tt_t + 2 * eps);
    }
}

// ---------------------------------------------------------------------
//  upper arm (J2 output, carries J3). Two halves split on the arm's
//  mid-plane; side = -1 drive half (motor side), +1 idle half.
// ---------------------------------------------------------------------
module ua_profile() {
    hull() { circle(r = ua_hub_r); translate([50, 0]) circle(r = ua_depth / 2); }
    hull() { translate([50, 0]) circle(r = ua_depth / 2); translate([L2 - 50, 0]) circle(r = ua_depth / 2); }
    hull() { translate([L2 - 50, 0]) circle(r = ua_depth / 2); translate([L2, 0]) circle(r = el_r); }
}

module ua_half_solid() {      // idle half (y >= 0)
    yo = ua_w / 2;
    yi = el_gap / 2;
    intersection() {
        rotate([-90, 0, 0]) linear_extrude(yo) ua_profile();
        translate([0, 0, -50]) linear_extrude(100)
            polygon([[-40, 0], [30, 0], [80, yi], [L2 + 40, yi], [L2 + 40, yo], [-40, yo]]);
    }
    translate([50, 0, 0]) rotate([-90, 0, 0]) cylinder(d = 12, h = 12);         // spacer boss
}

module upper_arm(side) {
    yo = ua_w / 2;
    halves_bolts = [[-18, 0], [10, 17], [10, -17], [50, 0]];
    difference() {
        mirror([0, side < 0 ? 1 : 0, 0]) ua_half_solid();
        if (side < 0) {
            // J2 keyed shaft
            translate([0, -yo - eps, 0]) rotate([-90, 0, 0]) shaft_bore(GM23_56, 30);
            translate([0, -20, 0]) rotate([180, 0, 0]) setscrew_m3(ua_hub_r + 1, 12);
            // J3 gearmotor on the elbow cheek
            translate([L2, -yo, 0]) rotate([-90, 0, 0]) gm_mount_cut(GM17_48, cheek_t, recess = gm_recess);
            for (p = halves_bolts) translate([p[0], -yo - eps, p[1]]) rotate([-90, 0, 0]) {
                cylinder(d = 4.4, h = ua_w);
                cylinder(d = 8, h = 6);
            }
        } else {
            // M8 pivot bolt: head captured on the split face, shank runs into the shoulder 608
            translate([0, -eps, 0]) rotate([-90, 0, 0]) {
                cylinder(d = 8.4, h = yo + 1);
                rotate(30) cylinder(d = (13 + 2 * clr) / cos(30), h = 6, $fn = 6);
            }
            // 608 at the elbow, pressed in from outside
            translate([L2, yo + eps, 0]) rotate([90, 0, 0]) {
                cylinder(d = B608[1] + bearing_fit, h = B608[2] + eps);
                cylinder(d = 12.5, h = cheek_t + 1);
            }
            for (p = halves_bolts) translate([p[0], yo + eps, p[1]]) rotate([90, 0, 0]) {
                cylinder(d = 4.4, h = ua_w);
                rotate(30) cylinder(d = 8.1, h = 5, $fn = 6);
            }
        }
    }
}

// ---------------------------------------------------------------------
//  forearm (J3 output, holds J4). Clamshell halves split on y = 0.
// ---------------------------------------------------------------------
module fa_profile() {
    hull() {
        circle(r = fa_hub_r);
        translate([32, -fa_h / 2]) square([j4_face_x + plate_t - 32, fa_h]);
    }
}

module forearm(side) {
    yo = fa_w / 2;
    pocket = gm_sq(GM17_34) + 0.8;
    bolts = [[62, 25], [62, -25], [90, 25], [90, -25], [116, 25], [116, -25], [-12, 13], [-12, -13]];
    difference() {
        mirror([0, side < 0 ? 1 : 0, 0]) rotate([-90, 0, 0]) linear_extrude(yo) fa_profile();
        // J4 gearmotor pocket + cable channel
        translate([j4_face_x - gm_len(GM17_34) - 1, -pocket / 2, -pocket / 2])
            cube([gm_len(GM17_34) + 1 + eps, pocket, pocket]);
        translate([fa_hub_r - 4, 0, 0]) rotate([0, 90, 0]) cylinder(d = 16, h = 40);
        translate([30, -6, 8]) cube([20, 12, fa_h]);                              // cable exit
        // J4 gearbox face plate
        translate([j4_face_x, 0, 0]) rotate([0, 90, 0]) gm_mount_cut(GM17_34, plate_t);
        if (side < 0) {
            translate([0, -yo - eps, 0]) rotate([-90, 0, 0]) shaft_bore(GM17_48, 20);
            translate([0, -yo + 10, 0]) rotate([180, 0, 0]) setscrew_m3(fa_hub_r + 1, 10);
            for (p = bolts) translate([p[0], -yo - eps, p[1]]) rotate([-90, 0, 0]) {
                cylinder(d = 3.4, h = fa_w);
                cylinder(d = 6.2, h = 3.5);
            }
        } else {
            translate([0, -eps, 0]) rotate([-90, 0, 0]) {
                cylinder(d = 8.4, h = yo + 1);
                rotate(30) cylinder(d = (13 + 2 * clr) / cos(30), h = 6, $fn = 6);
            }
            for (p = bolts) translate([p[0], yo + eps, p[1]]) rotate([90, 0, 0]) {
                cylinder(d = 3.4, h = fa_w);
                rotate(30) cylinder(d = 6.4, h = 3, $fn = 6);
            }
        }
    }
}

// ---------------------------------------------------------------------
//  wrist (J4 output, holds J5). Frame: origin = wrist centre,
//  X = forearm axis, Y = J5 axis, Z up.
// ---------------------------------------------------------------------
hub_x0 = j4_face_x + plate_t + hub_gap - L3;        // -31
hub_x1 = j4_face_x + gm_slen(GM17_34) - L3;         // -18

module wrist() {
    py = j5_face_y;
    difference() {
        union() {
            translate([hub_x0, 0, 0]) rotate([0, 90, 0]) cylinder(r = 12, h = hub_x1 - hub_x0);
            translate([hub_x0, py, -12]) cube([hub_x1 - hub_x0, -py, 24]);
            hull() {
                translate([hub_x0, py, -12]) cube([hub_x1 - hub_x0, plate_t, 24]);
                translate([0, py, 0]) rotate([-90, 0, 0]) cylinder(r = 22, h = plate_t);
            }
        }
        translate([hub_x0 - eps, 0, 0]) rotate([0, 90, 0]) rotate([0, 0, 90]) shaft_bore(GM17_34, hub_x1 - hub_x0 + 2 * eps);
        translate([(hub_x0 + hub_x1) / 2, 0, 0]) rotate([0, 0, 0]) setscrew_m3(13, 7.5);
        translate([0, py, 0]) rotate([-90, 0, 0]) gm_mount_cut(GM17_34, plate_t);
    }
}

// ---------------------------------------------------------------------
//  tool holder (J5 output). Frame: origin = wrist centre, Y = J5 axis,
//  tool points along -Z at J5 = 0. Holds a 12 mm shank; its top end
//  stops 24 mm below the wrist centre.
// ---------------------------------------------------------------------
tool_stop = 24;
clamp_len = 26;

module tool_holder() {
    y0 = j5_face_y + plate_t + hub_gap;              // -5
    y1 = j5_face_y + gm_slen(GM17_34);               //  8
    ro = tool_d / 2 + 5;
    difference() {
        union() {
            translate([0, y0, 0]) rotate([-90, 0, 0]) cylinder(r = 12, h = y1 - y0);
            translate([-7, -4, -tool_stop]) cube([14, 10, tool_stop - 6]);
            translate([0, 0, -tool_stop - clamp_len]) cylinder(r = ro, h = clamp_len);
            translate([ro - 5, -7, -tool_stop - clamp_len]) cube([12, 14, clamp_len]);   // pinch ear
        }
        translate([0, y0 - eps, 0]) rotate([-90, 0, 0]) rotate([0, 0, 180]) shaft_bore(GM17_34, y1 - y0 + 2 * eps);
        translate([0, (y0 + y1) / 2, 0]) setscrew_m3(13, 7.5);
        translate([0, 0, -tool_stop - clamp_len - eps]) cylinder(d = tool_d + 0.3, h = clamp_len + eps);
        translate([0, -1, -tool_stop - clamp_len - eps]) cube([ro + 10, 2, clamp_len + eps]);  // pinch slot
        translate([ro + 1.5, -8, -tool_stop - clamp_len / 2]) rotate([-90, 0, 0]) {
            cylinder(d = 3.4, h = 16);
            cylinder(d = 6.2, h = 3);
            translate([0, 0, 13]) rotate(30) cylinder(d = 6.4, h = 3.1, $fn = 6);
        }
    }
}

// ---------------------------------------------------------------------
//  small parts
// ---------------------------------------------------------------------
module spacer_m8() difference() { cylinder(d = 11.5, h = 4); translate([0, 0, -eps]) cylinder(d = 8.4, h = 4 + 2 * eps); }

// Holds a KW11 / SS-5GL microswitch (M2 holes 9.5 mm apart). Screw the base anywhere.
module endstop_clip() {
    difference() {
        union() { translate([-15, 0, 0]) cube([30, 12, 3]); translate([-15, 0, 0]) cube([30, 3, 16]); }
        for (x = [-10, 10]) hull() for (dy = [5.5, 9]) translate([x, dy, -eps]) cylinder(d = 3.4, h = 4);
        for (x = [-4.75, 4.75]) translate([x, -eps, 10]) rotate([-90, 0, 0]) cylinder(d = 2.2, h = 4);
    }
}

// Print this first. Check: 6008 and 608 press in, the gearbox pilot and screws
// fit, both shafts slide in, a heat-set insert sets cleanly. Adjust config.scad.
module fit_test() {
    t = 8;
    difference() {
        cube([165, 80, t]);
        translate([40, 40, 2]) cylinder(d = B6008[1] + bearing_fit, h = t);
        translate([40, 40, -eps]) cylinder(d = 60, h = t);
        translate([102, 40, 0]) gm_mount_cut(GM17_48, t);
        translate([145, 60, 2]) cylinder(d = B608[1] + bearing_fit, h = t);
        translate([145, 60, -eps]) cylinder(d = 12.5, h = t);
        translate([145, 24, -eps]) shaft_bore(GM23_56, t + 2 * eps);
        translate([102, 70, -eps]) shaft_bore(GM17_48, t + 2 * eps);
        translate([102, 9, t - insert_h]) cylinder(d = insert_d, h = insert_h + eps);
    }
}

// ---------------------------------------------------------------------
//  print orientations (flat face on the bed, z >= 0)
// ---------------------------------------------------------------------
module print_base_floor()        base_floor();
module print_base_shell()        translate([0, 0, shell_h]) rotate([180, 0, 0]) base_shell();
module print_j1_motor_mount()    translate([0, 0, -(tt_z - floor_t + j1_face)]) j1_motor_mount();
module print_j1_spigot()         rotate([180, 0, 0]) j1_spigot();
module print_j1_collar()         translate([0, 0, -(stack_bot - collar_h)]) j1_collar();
module print_turntable()         turntable();
module print_upper_arm_drive()   translate([0, 0, ua_w / 2]) rotate([90, 0, 0]) upper_arm(-1);
module print_upper_arm_idle()    translate([0, 0, ua_w / 2]) rotate([-90, 0, 0]) upper_arm(1);
module print_forearm_drive()     translate([0, 0, fa_w / 2]) rotate([90, 0, 0]) forearm(-1);
module print_forearm_idle()      translate([0, 0, fa_w / 2]) rotate([-90, 0, 0]) forearm(1);
module print_wrist()             translate([0, 0, -j5_face_y]) rotate([90, 0, 0]) wrist();
module print_tool_holder()       translate([0, 0, tool_stop + clamp_len]) tool_holder();
module print_spacer_m8()         spacer_m8();
module print_endstop_clip()      endstop_clip();
module print_fit_test()          fit_test();
