# -*- coding: utf-8 -*-
"""BipedDQN

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1RaYrA4rg9MyggIYkn5mBRr0kLXQDGfLd
"""

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F
from collections import namedtuple
from collections import deque
import random
import math

import pybullet as p
import pybullet_data

EPISODES = 3500

EPS = 1.0
EPS_DECAY = 0.995
EPS_MIN = 0.01

GAMMA = 0.8
LEARNING_RATE = 0.01
BATCH_SIZE = 64

TARGET_REWARD = 20000
TARGET_HEIGHT = 1

MOTOR_FORCE = 300

# 보상함수 가중치
M_W = 30
H_W = 10
E_W = 1


class DQN(nn.Module):
    def __init__(self, state_size, action_size):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(state_size, 64)
        self.fc2 = nn.Linear(64, 64)
        self.fc3 = nn.Linear(64, action_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = torch.relu(self.fc2(x))
        x = self.fc3(x)
        return x


class ReplayMemory:
    def __init__(self, capacity):
        self.memory = deque(maxlen=capacity)

    def push(self, transition):
        self.memory.append(transition)

    def sample(self, batch_size):
        return random.sample(self.memory, batch_size)

    def __len__(self):
        return len(self.memory)


class Agent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size

        self.model = DQN(state_size, action_size)
        self.target_model = DQN(state_size, action_size)
        self.target_model.load_state_dict(self.model.state_dict())
        self.memory = ReplayMemory(capacity=100000)
        self.optimizer = optim.Adam(self.model.parameters(), lr=LEARNING_RATE)

    def act(self, state):
        '''
        epsilon-greedy
        '''
        if np.random.rand() <= EPS:
      
            return tuple(random.choice([-1, 1]) for _ in range(self.action_size))
        else:
            state = torch.FloatTensor(state).unsqueeze(0)
            with torch.no_grad():
                q_values = self.model(state)

            return tuple(1 if q > 0 else -1 for q in q_values[0].cpu().numpy())

    def train(self, batch_size):
        if len(self.memory) < batch_size:
            return

        minibatch = self.memory.sample(batch_size)

        states = torch.FloatTensor(np.array([t[0] for t in minibatch]))
        actions = torch.LongTensor(np.array([t[1] for t in minibatch]).astype(int))
        rewards = torch.FloatTensor(np.array([t[2] for t in minibatch]))
        next_states = torch.FloatTensor(np.array([t[3] for t in minibatch]))
        dones = torch.FloatTensor(np.array([t[4] for t in minibatch]))

        q_values = self.model(states).gather(1, actions.unsqueeze(1)).squeeze(1)
        next_q_values = self.target_model(next_states).max(1)[0]
        targets = rewards + (GAMMA * next_q_values * (1 - dones))

        loss = nn.MSELoss()(q_values, targets)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        global EPS
        if EPS > EPS_MIN:
            EPS *= EPS_DECAY  # 학습 단계에서 EPS 감소

    def update_target_model(self):
        self.target_model.load_state_dict(self.model.state_dict())
        pass  


class Bot:
    def __init__(self, filename):
        p.connect(p.GUI)
        p.setGravity(0, 0, -9.8)
        p.setTimeStep(1/200)
        p.setAdditionalSearchPath(pybullet_data.getDataPath())
        self.plane = p.loadURDF("plane.urdf")
        self.actor = p.loadURDF(filename, basePosition=[0, 0, 1])
        pass

    def getJointState(self) -> list:
        '''
        get joint angle, velocity, torque
        '''
        num_joints = p.getNumJoints(self.actor)
        Joints = []
        Joints_raw = []
        JointState = namedtuple('JointState', ['angle', 'velocity', 'torque'])  # 복구된 namedtuple

        for joint_idx in range(num_joints):
            data = p.getJointState(self.actor, joint_idx)
            Joints_raw.append(data)
            angle = data[0]
            velocity = data[1]
            torque = data[3]
            Joints.append(JointState(angle=angle, velocity=velocity, torque=torque))

        return Joints, Joints_raw

    def getBodyState(self) -> list:
        '''
        get body state:
        [vx, vy, vz, x, y, z, qx, qy, qz, qw, wx, wy, wz] 
        '''
        Body = []
        position, orientation = p.getBasePositionAndOrientation(self.actor)
        linear_velocity, angular_velocity = p.getBaseVelocity(self.actor)

        Body.extend(linear_velocity)
        Body.extend(position)
        Body.extend(orientation)
        Body.extend(angular_velocity)
        return Body

    def getReward(self, state: tuple, joint_raw: list) -> float:
        '''
        calculate reward due to the state of the actor.
        '''
        moveReward = abs(state[0])
        heightPenalty = abs(state[5] - TARGET_HEIGHT)
        energy_penalty = sum(abs(js[1] * js[3]) for js in joint_raw)
        reward = M_W * moveReward - H_W * heightPenalty - E_W * energy_penalty
        return reward

    def step(self, action: tuple):
        '''
        apply thetas to actor
        '''
        for i, direction in enumerate(action):
            self.setJoint(i, direction)
        p.stepSimulation()

        bodyState = self.getBodyState()
        jointState, joint_raw = self.getJointState()
        new_state = (*bodyState, *jointState)

        reward = self.getReward(new_state, joint_raw)
        
        return new_state, reward

    def setJoint(self, jointIdx: int, direction: int) -> None:
        '''
        set actor joint angle by moving +5 or -5 degrees
        '''
        current_angle = p.getJointState(self.actor, jointIdx)[0]
        target_angle = current_angle + math.radians(5 * direction)
        p.setJointMotorControl2(
            bodyIndex=self.actor,
            jointIndex=jointIdx,
            controlMode=p.POSITION_CONTROL,
            targetPosition=target_angle,
            force=MOTOR_FORCE
        )
        pass  


state_size = 31
action_size = 6

agent = Agent(state_size, action_size)
#bot = Bot('dummy.urdf')  # urdf 파일 이름 넣기

for e in range(EPISODES):
    bot = Bot('dummy.urdf')
    state = np.zeros(state_size)
    total_reward = 0
    done = False

    while not done:
        bodyState = bot.getBodyState()
        jointState, _ = bot.getJointState()
        state = (*bodyState, *jointState)

        action = agent.act(state)
        next_state, reward = bot.step(action)
       

        agent.memory.push((state, action, reward, next_state, done))
        state = next_state
        total_reward += reward

        print('reward *******************************************************************************************= ',reward,done)

        if total_reward >= TARGET_REWARD:
            done = True

        if done:
            agent.update_target_model()
            print(f"Episode: {e+1}/{EPISODES}, Score: {total_reward}")
            break
    
    p.disconnect()
