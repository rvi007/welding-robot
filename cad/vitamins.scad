// =====================================================================
//  Ravi WR-1 - purchased parts ("vitamins"), modelled for the assembly
//  preview and the renders. Nothing in this file is printed.
//  Include after parts.scad (needs config.scad values).
//
//  MAT selects which material to draw, so each material can be exported
//  as its own mesh for the renderer: "all" draws everything in colour.
// =====================================================================

MAT = "all";

function mat_color(n) =
    n == "printed"  ? "#e8711a" :   // Ravi orange
    n == "printed2" ? "#30353d" :   // graphite
    n == "logo"     ? "#f4f4f4" :
    n == "alu"      ? "#c7cacf" :
    n == "black"    ? "#202226" :
    n == "steel"    ? "#a3a8ad" :
    n == "rubber"   ? "#141414" :
    n == "brass"    ? "#c9a04a" :
    n == "table"    ? "#4a4f56" :
    n == "block"    ? "#8a8f96" :
    n == "coupon"   ? "#7d8288" : "#888888";

module mat(n) if (MAT == "all" || MAT == n) color(mat_color(n)) children();

module chamfer_square(s, c) polygon([
    [-s / 2 + c, -s / 2], [s / 2 - c, -s / 2], [s / 2, -s / 2 + c], [s / 2, s / 2 - c],
    [s / 2 - c, s / 2], [-s / 2 + c, s / 2], [-s / 2, s / 2 - c], [-s / 2, -s / 2 + c]]);

// ---------------------------------------------------------------------
//  stepper motor: front face at z = 0, body towards -Z.
//  Cable outlet on the +X side of the rear cap.
// ---------------------------------------------------------------------
module stepper(size, len) {
    s     = size == 23 ? 56.4 : 42.3;
    c     = size == 23 ? 5.5 : 4.5;
    holes = size == 23 ? 47.14 : 31;
    fc    = size == 23 ? 9 : 7;
    rc    = size == 23 ? 11 : 9;
    mat("alu") difference() {
        translate([0, 0, -fc]) linear_extrude(fc) chamfer_square(s, c);
        for (x = [-1, 1], y = [-1, 1]) translate([x * holes / 2, y * holes / 2, -4])
            cylinder(d = size == 23 ? 4.5 : 3, h = 5, $fn = 16);
    }
    mat("black") translate([0, 0, -(len - rc)]) {
        linear_extrude(len - rc - fc) offset(delta = -0.35) chamfer_square(s, c);
    }
    mat("alu") difference() {
        translate([0, 0, -len]) linear_extrude(rc) chamfer_square(s, c);
        translate([0, 0, -len - 0.01]) linear_extrude(0.6) offset(delta = -6) chamfer_square(s, c);  // label recess
    }
    mat("logo") translate([0, 0, -len + 0.05]) linear_extrude(0.5) offset(delta = -6.6) chamfer_square(s, c);
    mat("steel") for (x = [-1, 1], y = [-1, 1])
        translate([x * holes / 2, y * holes / 2, -len - 1.2]) cylinder(d = size == 23 ? 6.5 : 5.4, h = 1.3, $fn = 20);
    mat("black") translate([s / 2 - 1, -7, -len + 1.5]) cube([6, 14, rc - 3]);
    mat("rubber") translate([s / 2 + 4.5, 0, -len + rc / 2]) rotate([0, 90, 0]) cylinder(d = 5, h = 8, $fn = 16);
}

// Output shaft: D-flat or key, from z = 0 up.
module output_shaft(g) {
    sd = gm_shaft(g);
    mat("steel") linear_extrude(gm_slen(g)) intersection() {
        circle(d = sd, $fn = 40);
        if (gm_key(g) == 0) translate([-sd, -sd]) square([2 * sd, sd + sd / 2 - gm_flat(g)]);
        else circle(d = sd, $fn = 40);
    }
    if (gm_key(g) > 0)
        mat("steel") translate([-gm_key(g) / 2, sd / 2 - 2.2, gm_pilot_h(g) + 3])
            cube([gm_key(g), gm_key(g) - 0.5, gm_slen(g) - gm_pilot_h(g) - 5]);
}

// Planetary gearbox: output face at z = 0, input flange at z = -len.
module planetary(g, len) {
    sq = gm_sq(g);
    d  = gm_face(g) > 50 ? 56 : gm_face(g);
    mat("black") difference() {
        union() {
            translate([0, 0, -len]) linear_extrude(7) chamfer_square(sq, sq > 50 ? 5.5 : 4.5);
            translate([0, 0, -len + 7]) cylinder(d = d, h = len - 7, $fn = 72);
            if (gm_face(g) > 50) translate([0, 0, -8]) linear_extrude(8) chamfer_square(gm_face(g), 4);
        }
        for (z = [-len * 0.42, -len * 0.62]) translate([0, 0, z])
            difference() { cylinder(d = d + 2, h = 1); cylinder(d = d - 1.6, h = 1, $fn = 72); }
        for (i = [0 : gm_n(g) - 1]) rotate(gm_a0(g) + i * 360 / gm_n(g))
            translate([gm_pcd(g) / 2, 0, -6]) cylinder(d = gm_bolt(g) * 0.85, h = 6.1, $fn = 16);
    }
    mat("alu") cylinder(d = gm_pilot(g), h = gm_pilot_h(g), $fn = 64);
    output_shaft(g);
}

// Complete gearmotor: output face at z = 0, shaft +Z, motor towards -Z.
module gearmotor_real(g) {
    size = gm_sq(g) > 50 ? 23 : 17;
    body = gm_len(g) > 110 ? 56 : (gm_len(g) > 80 ? 48 : 34);
    gb   = gm_len(g) - body;
    planetary(g, gb);
    translate([0, 0, -gb]) stepper(size, body);
}

// ---------------------------------------------------------------------
//  bearings and fasteners
// ---------------------------------------------------------------------
module bearing(b) {                        // axis Z, from z = 0 to width
    d = b[0]; D = b[1]; w = b[2];
    ri = d / 2 + (D - d) * 0.16;
    ro = D / 2 - (D - d) * 0.16;
    mat("steel") difference() { cylinder(d = D, h = w); translate([0, 0, -1]) cylinder(r = ro, h = w + 2); }
    mat("steel") difference() { cylinder(r = ri, h = w); translate([0, 0, -1]) cylinder(d = d, h = w + 2); }
    mat("rubber") translate([0, 0, 0.4]) difference() { cylinder(r = ro, h = w - 0.8); translate([0, 0, -1]) cylinder(r = ri, h = w + 2); }
}

module socket_head(m) {                    // head sits on z = 0, top at z = m
    mat("black") difference() {
        cylinder(d = 1.6 * m + 0.4, h = m, $fn = 32);
        translate([0, 0, m * 0.4]) cylinder(d = m * 0.9 / cos(30), h = m, $fn = 6);
    }
}

module hex_nut(m, h = undef) {
    mat("steel") difference() {
        cylinder(d = 1.75 * m / cos(30), h = is_undef(h) ? 0.8 * m : h, $fn = 6);
        translate([0, 0, -1]) cylinder(d = m, h = 2 * m, $fn = 24);
    }
}

module washer(m) mat("steel") difference() { cylinder(d = 2.1 * m, h = 0.2 * m); translate([0, 0, -1]) cylinder(d = m + 0.4, h = m); }

// Pointer used as the Phase 1 tool: 12 mm rod with a sharpened tip.
module pointer() {
    mat("alu") translate([0, 0, -TOOL + 10]) cylinder(d = tool_d, h = TOOL - tool_stop - 10);
    mat("steel") translate([0, 0, -TOOL]) cylinder(d1 = 0.8, d2 = tool_d, h = 10);
}

// ---------------------------------------------------------------------
//  work cell used in the renders: steel table, 96 mm block, T-joint coupon
//  matching jobs/fillet_straight.json (seam from X=280 to X=180 at Y=0, Z=100,
//  upright plate on the -Y side of the seam)
// ---------------------------------------------------------------------
module work_scene() {
    mat("table")  translate([-260, -380, -15]) cube([820, 760, 15]);
    mat("block")  translate([160, -95, 0]) cube([140, 190, 96]);
    mat("coupon") translate([170, -45, 96]) cube([120, 90, 4]);
    mat("coupon") translate([175, -4, 100]) cube([110, 4, 45]);
}
