#!/usr/bin/env python2.7
# license removed for brevity
import rospy
import numpy as np
import abc
import time

from rospy.numpy_msg import numpy_msg
from query_strategy import NoQuery, SimpleQuery, TargetedQuery
from feedback_cclfd.msg import Classification
from feedback_cclfd.msg import ConstraintTypes
from cairo_nlp.srv import STT, STTResponse, TTS, TTSResponse

""" This class queries the user for a plain English
    explanation about what the robot did wrong. It
    also uses the strategy pattern to switch between
    the following algorithms. You can set the query
    type in the launch files:
     1. No query
     2. Simple query
     3. Targeted Query"""


class QueryNLP():

    def __init__(self):
        rospy.init_node('query_nlp')

        # Get data from rosparam
        self.demo_filepath = rospy.get_param("DEMO_VOICE_FILEPATH")
        self.query_strategy = rospy.get_param("QUERY_STRATEGY")

        # Initialize subscriber
        rospy.Subscriber("/classifiers/synthesis", Classification, self.query)
        self.pub = rospy.Publisher("/planners/constraint_types",
                                   numpy_msg(ConstraintTypes),
                                   queue_size=10)

        # Set up client for NLP TTS service
        rospy.wait_for_service("/nlp/google/tts")
        try:
            self.tts_server = rospy.ServiceProxy(
                "/nlp/google/tts", TTS)
        except rospy.ServiceException:
            rospy.logwarn("Service setup failed (/nlp/google/tts)")

        # Set up client for NLP STT service
        rospy.wait_for_service("/nlp/google/stt")
        try:
            self.stt_server = rospy.ServiceProxy(
                "/nlp/google/stt", STT)
        except rospy.ServiceException:
            rospy.logerr("Service setup failed (/nlp/google/stt)")

    def main(self):
        rospy.loginfo("QUERY NLP: Starting...")
        rospy.spin()

    def query(self, msg):
        # Only query if synthesizer publishes false
        if not msg.classification:
            # Strategy pattern for different algorithms of querying
            query_question = ""

            if self.query_strategy == "none":
                rospy.loginfo("QUERY NLP: No query...")
                strategy = NoQuery()
                query_question = strategy.query_algorithm_interface(
                    msg.timestamp)

            if self.query_strategy == "simple":
                rospy.loginfo("QUERY NLP: Simple query...")
                strategy = SimpleQuery()
                query_question = strategy.query_algorithm_interface(
                    msg.timestamp)

            if self.query_strategy == "targeted":
                rospy.loginfo("QUERY NLP: Targeted query...")
                strategy = TargetedQuery()
                query_question = strategy.query_algorithm_interface(
                    msg.timestamp)

            # Create speech from text query
            self.tts_server(query_question)

            # Wait for response
            time.sleep(5)

            # Listen for response
            response = self.stt_server(
                self.demo_filepath + "/positive-constraint-comment.wav").output

            # Wait for response
            time.sleep(5)

            # Check if response was positive or negative
            if 'yes' in response.lower():
                rospy.loginfo("QUERY NLP: Positive response")
                feedback = True
            else:
                rospy.loginfo("QUERY NLP: Negative response")
                feedback = False

            # TODO: Modify constraint based on feedback

            # Run demonstration using given constraints
            constraints = ConstraintTypes()
            constraints.data = 0
            self.pub.publish(constraints)


if __name__ == '__main__':
    try:
        obj = QueryNLP()
        obj.main()
    except rospy.ROSInterruptException:
        pass
