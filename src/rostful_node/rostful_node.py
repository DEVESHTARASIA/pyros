from __future__ import absolute_import

import rospy

from .ros_interface import RosInterface

_ROCON_IF = False
try :
    from roconinterface.rocon_interface import RoconInterface
    _ROCON_IF = True
except Exception, e:
    rospy.logwarn('Missing rocon interface. Rocon features disabled')


from dynamic_reconfigure.server import Server
from rostful_node.cfg import RostfulNodeConfig
import ast


"""
Interface with ROS.
No inheritance to make sure destructor is called properly.
"""
class RostfulNode(object):
    def __init__(self, ros_args):
        #we initialize the node here, passing ros parameters
        rospy.init_node('rostful_server', argv=ros_args, anonymous=True, disable_signals=True)
        rospy.logwarn('rostful_server node started with args : %r', ros_args)

        enable_rocon = rospy.get_param('~enable_rocon', False)
        self.enable_rocon = enable_rocon or (
                (len(ast.literal_eval(rospy.get_param('~rapps_namespaces', "[]"))) > 0)
                or (len(ast.literal_eval(rospy.get_param('~interactions', "[]"))) > 0)
        )

        self.ros_if = RosInterface()

        if _ROCON_IF and self.enable_rocon:
            self.rocon_if = RoconInterface(self.ros_if)
        else:
            self.rocon_if = None

        # Create a dynamic reconfigure server.
        self.server = Server(RostfulNodeConfig, self.reconfigure)

    # Create a callback function for the dynamic reconfigure server.
    def reconfigure(self, config, level):
        rospy.logwarn("""Reconfigure Request: \renable_rocon : {enable_rocon}""".format(**config))
        self.enable_rocon = config["enable_rocon"] or (
            len(ast.literal_eval(config["rapps_namespaces"])) > 0
            or len(ast.literal_eval(config["interactions"])) > 0
        )

        if _ROCON_IF and not self.rocon_if and self.enable_rocon:
            self.rocon_if = RoconInterface(self.ros_if)

        config = self.ros_if.reconfigure(config, level)

        if _ROCON_IF and self.rocon_if:
            config = self.rocon_if.reconfigure(config, level)

        return config

    def spin(self):
        rate = rospy.Rate(10)  # 10hz
        while not rospy.is_shutdown():
            # do stuff here only if needed in emergency.
            # Async event based programming is preferred.
            # but we might want to have an update loop from here to avoid too many threads.
            rate.sleep()  # loop timer only here
        rospy.spin()

    """
    Does all necessary cleanup to bring down RosInterface
    """
    def __del__(self):
        rospy.logwarn('rostful_server node stopped')
        rospy.signal_shutdown('Closing')


