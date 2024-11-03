import pybullet as p
import pybullet_data
import time

# PyBullet 연결 및 GUI 환경 설정
p.connect(p.GUI)

# PyBullet 내장 데이터 경로 설정
p.setAdditionalSearchPath(pybullet_data.getDataPath())

# 평평한 바닥 로드
p.loadURDF("plane.urdf")

# 중력 설정 (지면으로 끌어당기기 위함)
p.setGravity(0, 0, -9.8)

# URDF 파일 로드 (경로에 저장한 simple_biped.urdf 파일)
robot_id = p.loadURDF("dummy.urdf", [0, 0, 0.5], useFixedBase=False)


while True:
    p.stepSimulation()  # 물리 시뮬레이션 한 스텝 진행
    time.sleep(10000)  # 시뮬레이션 속도 맞추기 (240Hz 기준)
    print('heool')



