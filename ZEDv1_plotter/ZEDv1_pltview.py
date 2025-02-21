#!/usr/bin/env python3

import sys
import pyzed.sl as sl
import argparse
import os
from datetime import datetime

# Custom vertex shader for depth-based RGB coloring
POINTCLOUD_VERTEX_SHADER = """
#version 330 core
layout(location = 0) in vec4 in_VertexRGBA;
uniform mat4 u_mvpMatrix;
out vec4 b_color;

void main() {
    // Calculate depth (distance from camera)
    float depth = length(in_VertexRGBA.xyz);
    
    // Create color based on depth
    vec3 color;
    float min_depth = 0.5;  // meters
    float max_depth = 10.0; // meters
    
    // Normalize depth to [0,1]
    float normalized_depth = clamp((depth - min_depth) / (max_depth - min_depth), 0.0, 1.0);
    
    // Create RGB gradient: red (close) → green (middle) → blue (far)
    if (normalized_depth < 0.33) {
        // Red to Yellow gradient (closest third)
        color = vec3(1.0, normalized_depth * 3.0, 0.0);
    } else if (normalized_depth < 0.67) {
        // Yellow to Green to Cyan (middle third)
        float t = (normalized_depth - 0.33) * 3.0;
        color = vec3(1.0 - t, 1.0, t);
    } else {
        // Cyan to Blue gradient (farthest third)
        float t = (normalized_depth - 0.67) * 3.0;
        color = vec3(0.0, 1.0 - t, 1.0);
    }
    
    b_color = vec4(color, 1.0);
    gl_Position = u_mvpMatrix * vec4(in_VertexRGBA.xyz, 1);
}
"""

# Basic fragment shader
POINTCLOUD_FRAGMENT_SHADER = """
#version 330 core
in vec4 b_color;
layout(location = 0) out vec4 out_Color;
void main() {
   out_Color = b_color;
}
"""


def parse_args(init, opt):
    """Parse command line arguments and configure ZED initialization parameters"""
    if len(opt.input_svo_file) > 0 and opt.input_svo_file.endswith(".svo"):
        init.set_from_svo_file(opt.input_svo_file)
        print("[Sample] Using SVO File input: {0}".format(opt.input_svo_file))
    elif len(opt.ip_address) > 0:
        ip_str = opt.ip_address
        if ip_str.replace(':', '').replace('.', '').isdigit() and len(ip_str.split('.')) == 4 and len(ip_str.split(':')) == 2:
            init.set_from_stream(ip_str.split(':')[0], int(ip_str.split(':')[1]))
            print("[Sample] Using Stream input, IP: ", ip_str)
        elif ip_str.replace(':', '').replace('.', '').isdigit() and len(ip_str.split('.')) == 4:
            init.set_from_stream(ip_str)
            print("[Sample] Using Stream input, IP: ", ip_str)
        else:
            print("Invalid IP format. Using live stream")
            
    if "HD2K" in opt.resolution:
        init.camera_resolution = sl.RESOLUTION.HD2K
        print("[Sample] Using Camera in resolution HD2K")
    elif "HD1200" in opt.resolution:
        init.camera_resolution = sl.RESOLUTION.HD1200
        print("[Sample] Using Camera in resolution HD1200")
    elif "HD1080" in opt.resolution:
        init.camera_resolution = sl.RESOLUTION.HD1080
        print("[Sample] Using Camera in resolution HD1080")
    elif "HD720" in opt.resolution:
        init.camera_resolution = sl.RESOLUTION.HD720
        print("[Sample] Using Camera in resolution HD720")
    elif "SVGA" in opt.resolution:
        init.camera_resolution = sl.RESOLUTION.SVGA
        print("[Sample] Using Camera in resolution SVGA")
    elif "VGA" in opt.resolution:
        init.camera_resolution = sl.RESOLUTION.VGA
        print("[Sample] Using Camera in resolution VGA")
    elif len(opt.resolution) > 0:
        print("[Sample] No valid resolution entered. Using default")
    else:
        print("[Sample] Using default resolution")


def setup_opengl_viewer():
    """Import the viewer module and modify it with our custom shaders"""
    import ogl_viewer as gl
    
    # Inject our custom shader into the viewer module
    gl.POINTCLOUD_VERTEX_SHADER = POINTCLOUD_VERTEX_SHADER
    gl.POINTCLOUD_FRAGMENT_SHADER = POINTCLOUD_FRAGMENT_SHADER
    
    return gl


def main():
    """Main function to run ZED point cloud visualization and recording"""
    # Create output directory for point clouds
    save_dir = "point_clouds"
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    print("\nZED Point Cloud Viewer with RGB Depth Gradient")
    print("----------------------------------------------")
    print("Depth coloring: RED (close) → GREEN (middle) → BLUE (far)")
    print("\nControls:")
    print("Press 'Esc' to quit")
    print("Press 's' to save a point cloud")
    print("Press 'r' to enable/disable continuous recording")
    print("Use mouse wheel to zoom in/out")
    print("Use mouse to rotate the view")

    # Initialize ZED camera
    init_params = sl.InitParameters(
        depth_mode=sl.DEPTH_MODE.ULTRA,
        coordinate_units=sl.UNIT.METER,
        coordinate_system=sl.COORDINATE_SYSTEM.RIGHT_HANDED_Y_UP,
        depth_minimum_distance=0.3,
        depth_maximum_distance=15.0
    )
    parse_args(init_params, opt)
    
    # Open ZED camera
    zed = sl.Camera()
    status = zed.open(init_params)
    if status != sl.ERROR_CODE.SUCCESS:
        print(f"Error opening ZED camera: {status}")
        exit()

    # Set resolution for point cloud
    res = sl.Resolution()
    res.width = 720
    res.height = 404

    # Get camera model for 3D visualization
    camera_model = zed.get_camera_information().camera_model
    
    # Setup OpenGL viewer with our custom shaders
    gl = setup_opengl_viewer()
    viewer = gl.GLViewer()
    viewer.init(1, sys.argv, camera_model, res)

    # Create point cloud object
    point_cloud = sl.Mat(res.width, res.height, sl.MAT_TYPE.F32_C4, sl.MEM.CPU)
    
    # Flag for continuous recording
    recording_enabled = False
    frame_count = 0
    
    # Main loop
    while viewer.is_available():
        if zed.grab() == sl.ERROR_CODE.SUCCESS:
            # Retrieve point cloud from ZED camera
            zed.retrieve_measure(point_cloud, sl.MEASURE.XYZRGBA, sl.MEM.CPU, res)
            
            # Update viewer with new point cloud data
            viewer.updateData(point_cloud)
            
            # Save single point cloud if requested
            if viewer.save_data:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = os.path.join(save_dir, f"pointcloud_{timestamp}.ply")
                
                # Save at full resolution
                point_cloud_to_save = sl.Mat()
                zed.retrieve_measure(point_cloud_to_save, sl.MEASURE.XYZRGBA, sl.MEM.CPU)
                err = point_cloud_to_save.write(filename)
                
                if err == sl.ERROR_CODE.SUCCESS:
                    print(f"Point cloud saved to: {filename}")
                else:
                    print(f"Failed to save point cloud: {err}")
                    
                viewer.save_data = False

            # Check for 'r' key press to toggle recording
            if hasattr(viewer, 'key_pressed') and viewer.key_pressed == ord('r'):
                recording_enabled = not recording_enabled
                if recording_enabled:
                    print("Continuous recording ENABLED")
                    frame_count = 0
                else:
                    print(f"Continuous recording DISABLED. Saved {frame_count} frames.")
                viewer.key_pressed = 0  # Reset key press state
                
            # Handle continuous recording
            if recording_enabled:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(save_dir, f"pointcloud_{timestamp}.ply")
                
                # Save at full resolution
                point_cloud_to_save = sl.Mat()
                zed.retrieve_measure(point_cloud_to_save, sl.MEASURE.XYZRGBA, sl.MEM.CPU)
                err = point_cloud_to_save.write(filename)
                
                if err == sl.ERROR_CODE.SUCCESS:
                    frame_count += 1
                    print(f"Recording frame {frame_count}: {filename}", end="\r")
                else:
                    print(f"\nFailed to save frame: {err}")

    # Clean up
    viewer.exit()
    zed.close()
    print("\nApplication closed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input_svo_file', type=str, help='Path to an .svo file, if you want to replay it', default='')
    parser.add_argument('--ip_address', type=str, help='IP Address, in format a.b.c.d:port or a.b.c.d', default='')
    parser.add_argument('--resolution', type=str, help='Resolution, can be either HD2K, HD1200, HD1080, HD720, SVGA or VGA', default='')
    opt = parser.parse_args()
    
    if len(opt.input_svo_file) > 0 and len(opt.ip_address) > 0:
        print("Specify only input_svo_file or ip_address, or none to use wired camera, not both. Exit program")
        exit()
        
    main()