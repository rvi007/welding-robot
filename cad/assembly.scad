// Ravi WR-1 - full assembly preview. Open in OpenSCAD and change the joint
// angles below (same conventions as the software, degrees).

include <parts.scad>

q1 = 20;    // base yaw
q2 = 35;    // shoulder (0 = upper arm vertical, + forward)
q3 = 20;    // elbow (0 = forearm square to upper arm, + down)
q4 = 0;     // forearm roll
q5 = -10;   // wrist pitch (0 = tool square to forearm)

show_motors     = true;
show_work_block = true;

module printed() color("#3b6ea5") children();
module printed2() color("#5b8cc4") children();

module robot(q1, q2, q3, q4, q5) {
    printed() base_floor();
    printed2() translate([0, 0, floor_t]) base_shell();
    printed() translate([0, 0, floor_t]) j1_motor_mount();
    if (show_motors) translate([0, 0, tt_z + j1_face]) gearmotor(GM17_48);

    rotate([0, 0, q1]) {
        translate([0, 0, tt_z]) {
            printed() turntable();
            printed2() { j1_spigot(); j1_collar(); }
            if (show_motors) translate([0, -sh_gap / 2 - cheek_t, sh_az]) rotate([-90, 0, 0]) gearmotor(GM23_56);
        }
        translate([0, 0, d1]) rotate([0, q2, 0]) {
            rotate([0, -90, 0]) {
                printed() upper_arm(-1);
                printed2() upper_arm(1);
                if (show_motors) translate([L2, -ua_w / 2 + gm_recess, 0]) rotate([-90, 0, 0]) gearmotor(GM17_48);
            }
            translate([0, 0, L2]) rotate([0, q3, 0]) {
                printed() forearm(-1);
                printed2() forearm(1);
                if (show_motors) translate([j4_face_x, 0, 0]) rotate([0, 90, 0]) gearmotor(GM17_34);
                translate([L3, 0, 0]) rotate([q4, 0, 0]) {
                    printed() wrist();
                    if (show_motors) translate([0, j5_face_y, 0]) rotate([-90, 0, 0]) gearmotor(GM17_34);
                    rotate([0, q5, 0]) {
                        printed2() tool_holder();
                        color("#e07b24") translate([0, 0, -TOOL]) cylinder(d = tool_d, h = TOOL - tool_stop);
                    }
                }
            }
        }
    }
}

robot(q1, q2, q3, q4, q5);
if (show_work_block) color("#b8b8b8", 0.6) translate([150, -100, 0]) cube([160, 200, 100]);
