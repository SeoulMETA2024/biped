import numpy as np


class Kinematics:
    #https://ddangeun.tistory.com/27 2DOF manipulator kinematics 수식 참고
    def __init__(self, l1, l2):
        
        self.L1 = l1
        self.L2 = l2
        pass

    def forwardKinematics(self,theta1,theta2):
        
        x = self.L1 * np.cos(theta1) + self.L2 * np.cos(theta1+theta2)
        y = self.L1 * np.sin(theta1) + self.L2 * np.cos(theta1+theta2)

        return (x,y)
    
    def inverseKinematics(self,x,y):


        cos_theta2 = (x**2+y**2-self.L1**2-self.L2**2)/(2*self.L1*self.L2)

        sin_theta2 = np.sqrt(1-cos_theta2**2)
        theta2 = np.arctan2(sin_theta2,cos_theta2)
        theta1 = np.arctan2(y,x) - np.arctan2(self.L1 + self.L2*cos_theta2,self.L2*sin_theta2) 
        return (theta1, theta2)
