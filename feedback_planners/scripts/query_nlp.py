#!/usr/bin/env python2.7
# license removed for brevity
import rospy
import numpy as np
import abc

from feedback_classifiers.msg import Classification
from rospy.numpy_msg import numpy_msg
from feedback_planners.msg import ConstraintTypes
from QueryStrategy import NoQuery, SimpleQuery, TargetedQuery
from feedback_planners.srv import TTS, TTSResponse


""" This class queries the user for a plain English
    explanation about what the robot did wrong. It
    also uses the strategy pattern to switch between
    the following algorithms:
     1. Simple query
     2. Targeted Query"""


class QueryNLP():

    def __init__(self):
        rospy.init_node('query_nlp')

        self.query_strategy = rospy.get_param("QUERY_STRATEGY")

        # Initialize subscriber
        rospy.Subscriber("/classifiers/synthesis", Classification, self.query)
        self.pub = rospy.Publisher("/planners/constraint_types",
                                   numpy_msg(ConstraintTypes),
                                   queue_size=10)

        # Set up client for NLP TTS service
        rospy.wait_for_service("/nlp/tts")
        try:
            self.tts_server = rospy.ServiceProxy(
                "/nlp/tts", TTS)
            rospy.loginfo("Service setup succeeded (/nlp/tts)")
        except rospy.ServiceException:
            rospy.logwarn("Service setup failed (/nlp/tts)")

    def run(self):
        while(not rospy.is_shutdown()):
            # keep running to check for info on sub
            pass

    def query(self, msg):

        # TODO: connect to text-to-speech api/command

        # Only query if synthesizer publishes false
        if not msg.classification:

            query_question = ""
            if self.query_strategy == "simple":
                rospy.loginfo("QUERY NLP: No query...")

                # check the usage
                # Strategy pattern for different algorithms of querying
                strategy = SimpleQuery()
                query_question = strategy.query_algorithm_interface(
                    msg.timestamp)

            if self.query_strategy == "targeted":
                rospy.loginfo("QUERY NLP: Querying using targeted...")

                # check the usage
                # Strategy pattern for different algorithms of querying
                strategy = TargetedQuery()
                query_question = strategy.query_algorithm_interface(
                    msg.timestamp)

            # Create speech from text query
            self.tts_server(query_question)

            # Run demonstration using given constraints
            constraints = ConstraintTypes()
            constraints.data = 0
            self.pub.publish(constraints)


if __name__ == '__main__':
    try:
        obj = QueryNLP()
        obj.run()
    except rospy.ROSInterruptException:
        pass
