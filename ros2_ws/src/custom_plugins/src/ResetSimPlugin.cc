#include "custom_plugins/ResetSimPlugin.hh" // Include the ResetSimPlugin header file here
#include <gz/plugin/Register.hh>
#include <gz/sim/components/Model.hh>
#include <gz/sim/components/Name.hh>
#include <gz/sim/components/Pose.hh>
#include <gz/math/Pose3.hh>
#include <gz/sim/components/PoseCmd.hh>
#include <gz/sim/components/World.hh>
#include <gz/sim/components/Joint.hh>
#include <gz/sim/components/ParentEntity.hh>
#include <gz/sim/components/JointPositionReset.hh>
#include <gz/sim/components/JointVelocityReset.hh>
#include <gz/sim/components/Static.hh>

#include <gz/common/Console.hh>

#include <rclcpp/rclcpp.hpp>

// Lets me use reset_plugin methods without having to write reset_plugin:: 
// every time
using namespace reset_plugin;

// Good practice to comment out passed in variables we won't use to stop the 
// compiler from throwing warnings
/**
 * @brief Configure() is called when the plugin is loaded
 * @param none
 * @retval none
 */
void ResetSimPlugin::Configure(
    const gz::sim::Entity &/*_entity*/,
    const std::shared_ptr<const sdf::Element> &/*_sdf*/,
    gz::sim::EntityComponentManager &/*_ecm*/,
    gz::sim::EventManager &/*_eventMgr*/)
{   
    // Subscribe to the GUI's keystroke topic
    if (this->node.Subscribe("/keyboard/keypress", &ResetSimPlugin::OnKeyPress, this))
    {
        std::cout << "[ResetSimPlugin] Successfully subscribed to keyboard "
                     "events!" << std::endl;
    }
    else
    {
        std::cout << "[ResetSimPlugin] Failed to subscribe to keyboard "
                     "topic." << std::endl; 
    }
}


/**
 * @brief callback for keyboard pressed
 * @param _msg : reference to key pressed variable
 * @retval none
 */
void ResetSimPlugin::OnKeyPress(const gz::msgs::Int32 &_msg)
{
    // ASCII value for r and R
    if (_msg.data() == 114 || _msg.data() == 82) 
    {   
        // gzerr << "Key pressed! Updating flag on object at: " << this << std::endl;
        this->teleport_requested = true;
    }
}


/**
 * @brief runs on every simulation frame. We use it to reset the simulation.
 * @param _ecm
 * @retval 
 */
void ResetSimPlugin::PreUpdate(
    const gz::sim::UpdateInfo &/*_info*/, 
    gz::sim::EntityComponentManager &_ecm)
{   
    // ====================================================================
    // PHASE 1: THE STARTUP SNAPSHOT (Runs only at the very beginning)
    // ====================================================================
    if (!this->startup_memorized)
    {
        bool found_dynamic_model = false;

        // 1. Check if any dynamic models have successfully spawned yet
        // TODO: This assumes that if one dyamic model has been found all 
        //       the other dynamic models have also been spawned
        _ecm.Each<gz::sim::components::Model>(
            [&](const gz::sim::Entity &_modelEntity,
                const gz::sim::components::Model *) -> bool
            {
                const auto *staticComp = 
                    _ecm.Component<gz::sim::components::Static>(_modelEntity);
                bool is_static = staticComp ? staticComp->Data() : false;

                if (!is_static) found_dynamic_model = true;
                return true; 
            });

        // 2. Take the permanent snapshot!
        if (found_dynamic_model)
        {
            _ecm.Each<gz::sim::components::Model, 
                        gz::sim::components::Pose, 
                        gz::sim::components::Name>(
                [&](const gz::sim::Entity &_modelEntity,
                    const gz::sim::components::Model *,
                    const gz::sim::components::Pose *_poseComp,
                    const gz::sim::components::Name *_nameComp) -> bool
                {
                    const auto *staticComp = 
                        _ecm.Component<gz::sim::components::Static>(_modelEntity);
                    bool is_static = staticComp ? staticComp->Data() : false;

                    if (!is_static)
                    {
                        this->initial_poses[_modelEntity] = _poseComp->Data();
                        std::cout << "[ResetSimPlugin] Startup snapshot "
                                        "saved for: " 
                                        << _nameComp->Data() << std::endl;
                    }
                    return true;
                });

            // 3. Lock the system forever
            this->startup_memorized = true;
            std::cout << "[ResetSimPlugin] Startup sequence complete. "
                            "Memory locked." << std::endl;
        }
        
        // Do not process any keyboard resets while the simulation is still 
        // setting up
        this->teleport_requested = false;
        return; 
    }

    // ====================================================================
    // PHASE 2: THE RESETTER (Only runs if teleport is requested)
    // ====================================================================
    if (!this->teleport_requested)
        return;

    bool found_something_to_reset = false;

    for (auto const& [robot_entity, original_pose] : this->initial_poses)
    {
        if (_ecm.HasEntity(robot_entity))
        {
            std::cout << "Entity resetting." << std::endl;
            found_something_to_reset = true;

            // Teleport back to the settled snapshot
            _ecm.SetComponentData<gz::sim::components::WorldPoseCmd>(robot_entity, original_pose);

            // Reset joints
            _ecm.Each<gz::sim::components::Joint, gz::sim::components::ParentEntity>(
                [&](const gz::sim::Entity &_jointEntity,
                    const gz::sim::components::Joint *,
                    const gz::sim::components::ParentEntity *_parent) -> bool
                {
                    if (_parent->Data() == robot_entity)
                    {
                        _ecm.SetComponentData<gz::sim::components::JointPositionReset>(_jointEntity, {0.0});
                        _ecm.SetComponentData<gz::sim::components::JointVelocityReset>(_jointEntity, {0.0});
                    }
                    return true; 
                });
        }
    }

    if (found_something_to_reset) {
        std::cout << "[ResetSimPlugin] Successfully teleported agents to "
                     "settled spawn points!" << std::endl;
    } else {
        std::cout << "[ResetSimPlugin] Reset Failed: No dynamic models found "
                     "in memory!" << std::endl;
    }

    this->teleport_requested = false;
}


// @note register the class as a Gazebo plugin
GZ_ADD_PLUGIN (
    reset_plugin::ResetSimPlugin,
    gz::sim::System,
    gz::sim::ISystemConfigure,
    gz::sim::ISystemPreUpdate
)