import nengo
import numpy as np
from multicopter_sim import Multicopter

# Target 
ALTITUDE_TARGET = 10

# PID params
KP = 0.4
KD = 10.0
KI = 0.03

# Network params
SIM_TIME         = 0.001
N_NEURONS        = 200
INTEGRAL_SYNAPSE = 0.1
INTEGRAL_RADIUS  = 2

q_value = 0
q_target_value = 0
dq_value = 0
last_actual = 0
output_value = 0

model = nengo.Network(seed=3)

with model:
    
    # Create a multicopter and start communications with simulator
    copter = Multicopter()
    copter.start()
    
    q_target = nengo.Node(lambda t: q_target_value, label='q_target')
    q = nengo.Node(lambda t: q_value, label='q')
    dq = nengo.Node(lambda t: dq_value, label='dq')

    dq_target = nengo.Node(None, size_in=1, label='dq_target')
    nengo.Connection(q_target, dq_target, synapse=None, transform=1) # direct feed-forward synapse
    nengo.Connection(q_target, dq_target, synapse=0, transform=-1)   # minimal time-step delay

    q_err = nengo.Ensemble(n_neurons=N_NEURONS, dimensions=1, label='q_err')
    nengo.Connection(q_target, q_err, synapse=None)
    nengo.Connection(q, q_err, synapse=None, transform=-1)

    q_err_integral = nengo.Ensemble(n_neurons=N_NEURONS, dimensions=1, radius=INTEGRAL_RADIUS,
            label='q_err_integral')
    nengo.Connection(q_err, q_err_integral, synapse=INTEGRAL_SYNAPSE, transform=INTEGRAL_SYNAPSE)
    nengo.Connection(q_err_integral, q_err_integral, synapse=INTEGRAL_SYNAPSE, transform=1)

    x = nengo.Ensemble(n_neurons=1200, dimensions=3, radius=30)

    u = nengo.Node(None, size_in=1, label='u')    # output
    
    nengo.Connection(q_err, u, transform=KP, synapse=None)

    nengo.Connection(q_err_integral, u, transform=KI, synapse=None)
    
    dq_err = nengo.Ensemble(n_neurons=N_NEURONS, dimensions=1, label='dq_err')
    nengo.Connection(dq_target, dq_err, synapse=None)
    nengo.Connection(dq, dq_err, synapse=None, transform=-1)

    def loop(u):

        # Get vehicle state from sim
        telem = copter.getState()

        # Extract time from state
        #t =  telem[0]

        # Extract altitude from state.  Altitude is in NED coordinates, so we negate it to use as input
        # to PID controller.
        #z = -telem[9]

        copter.setMotors(0.4*np.ones(4))        

        return u
    
    nengo.Connection(dq_err, u, transform=KD, synapse=None, function=loop)
