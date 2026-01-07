import os

import launch
import launch.actions
import launch.events

import launch_ros
import launch_ros.actions
import launch_ros.events

from launch import LaunchDescription
from launch_ros.actions import LifecycleNode

import lifecycle_msgs.msg

from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    ld = launch.LaunchDescription()

    # --- args ---
    ld.add_action(launch.actions.DeclareLaunchArgument(
        'cloud_topic',
        default_value='/velodyne_points',
        description='Input PointCloud2 topic name for /cloud'
    ))
    ld.add_action(launch.actions.DeclareLaunchArgument(
        'imu_topic',
        default_value='/imu/data',
        description='Input IMU topic name for /imu'
    ))
    ld.add_action(launch.actions.DeclareLaunchArgument(
        'odom_topic',
        default_value='/odom',
        description='Input Odometry topic name for /odom'
    ))
    ld.add_action(launch.actions.DeclareLaunchArgument(
        'localization_param_file',
        default_value=os.path.join(
            get_package_share_directory('lidar_localization_ros2'),
            'param',
            'localization.yaml'
        ),
        description='Path to localization param yaml'
    ))

    cloud_topic = launch.substitutions.LaunchConfiguration('cloud_topic')
    imu_topic   = launch.substitutions.LaunchConfiguration('imu_topic')
    odom_topic  = launch.substitutions.LaunchConfiguration('odom_topic')
    param_file  = launch.substitutions.LaunchConfiguration('localization_param_file')

    lidar_localization = launch_ros.actions.LifecycleNode(
        name='lidar_localization',
        namespace='',
        package='lidar_localization_ros2',
        executable='lidar_localization_node',
        parameters=[param_file],
        remappings=[
            ('/cloud', cloud_topic),
            ('/imu',   imu_topic),
            ('/odom',  odom_topic),
        ],
        output='screen'
    )

    to_inactive = launch.actions.EmitEvent(
        event=launch_ros.events.lifecycle.ChangeState(
            lifecycle_node_matcher=launch.events.matches_action(lidar_localization),
            transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
        )
    )

    from_unconfigured_to_inactive = launch.actions.RegisterEventHandler(
        launch_ros.event_handlers.OnStateTransition(
            target_lifecycle_node=lidar_localization,
            goal_state='unconfigured',
            entities=[
                launch.actions.LogInfo(msg="-- Unconfigured --"),
                launch.actions.EmitEvent(event=launch_ros.events.lifecycle.ChangeState(
                    lifecycle_node_matcher=launch.events.matches_action(lidar_localization),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_CONFIGURE,
                )),
            ],
        )
    )

    from_inactive_to_active = launch.actions.RegisterEventHandler(
        launch_ros.event_handlers.OnStateTransition(
            target_lifecycle_node=lidar_localization,
            start_state = 'configuring',
            goal_state='inactive',
            entities=[
                launch.actions.LogInfo(msg="-- Inactive --"),
                launch.actions.EmitEvent(event=launch_ros.events.lifecycle.ChangeState(
                    lifecycle_node_matcher=launch.events.matches_action(lidar_localization),
                    transition_id=lifecycle_msgs.msg.Transition.TRANSITION_ACTIVATE,
                )),
            ],
        )
    )
    
    ld.add_action(from_unconfigured_to_inactive)
    ld.add_action(from_inactive_to_active)

    ld.add_action(lidar_localization)

    ld.add_action(to_inactive)

    return ld