#pragma once

#include <gz/sim/System.hh> 
#include <gz/sim/Entity.hh>
#include <gz/sim/EntityComponentManager.hh>
#include <gz/transport/Node.hh>
#include <gz/msgs/int32.pb.h>
#include <atomic>

namespace reset_plugin
{

class ResetSimPlugin :
    public gz::sim::System,
    public gz::sim::ISystemConfigure,
    public gz::sim::ISystemPreUpdate
    {   
        public:
            // Constructor
            ResetSimPlugin() = default;

            // ISystemConfigure reset method - Configure runs once on startup
            // Configure runs once at startup
            void Configure(const gz::sim::Entity &_entity,
                           const std::shared_ptr<const sdf::Element> &_sdf,
                           gz::sim::EntityComponentManager &_ecm,
                           gz::sim::EventManager &_eventMgr) override;

            // PreUpdate runs on every physics frame
            void PreUpdate(const gz::sim::UpdateInfo &_info, 
                           gz::sim::EntityComponentManager &_ecm) override;

        private:
            // Function to handle logic for recieving a key press
            void OnKeyPress(const gz::msgs::Int32 &_msg);
            
            // Creation of a node for the plugin that will subscribe to the keypress topic
            gz::transport::Node node;

            // THE STARTUP LOCK
            bool startup_memorized = false;
            int settling_counter = 0;

            // THE MEMORY BANK
            std::unordered_map<gz::sim::Entity, gz::math::Pose3d> initial_poses;
            
            // A thread-safe flag to tell the physics thread to teleport the robot
            std::atomic<bool> teleport_requested{false};
    };
}
