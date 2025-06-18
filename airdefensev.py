import simpy
import math
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# إعداد الرادار
radar_range = 80000  # 50 km
radar_x, radar_y = 0, 0

# إعداد الصواريخ
missiles = [
    {'name': 'Fattah-1', 'x': 200000, 'y': 250000, 'speed_x': -5100, 'speed_y': -5100, 'color': 'blue', 'hit': False},
    {'name': 'Rezvan', 'x': 210000, 'y': 240000, 'speed_x': -4400, 'speed_y': -4300, 'color': 'green', 'hit': False},
]

interceptors_data = []  # Store all interceptor positions for visualization
active_interceptors = []  # Store active interceptor objects
distances = []

def missile(env, missile_data):
    while not missile_data['hit']:
        distance = math.sqrt((missile_data['x'] - radar_x)**2 + (missile_data['y'] - radar_y)**2)
        distances.append((missile_data['name'], env.now, distance))
        
        # Check if missile is within radar range and launch interceptor
        if distance <= radar_range and not missile_data.get('interceptor_launched', False):
            print(f" Missile {missile_data['name']} detected at time {env.now} sec, distance: {distance:.0f}m")
            interceptor_obj = {
                'x': radar_x, 
                'y': radar_y, 
                'target': missile_data,
                'speed': 7000,  # Interceptor speed
                'active': True
            }
            active_interceptors.append(interceptor_obj)
            env.process(interceptor(env, interceptor_obj))
            missile_data['interceptor_launched'] = True
        
        # Update missile position
        missile_data['x'] += missile_data['speed_x']
        missile_data['y'] += missile_data['speed_y']
        
        # Check if missile hit the ground
        if missile_data['y'] <= 0:
            print(f" Missile {missile_data['name']} hit the ground at time {env.now} sec")
            missile_data['hit'] = True
            missile_data['color'] = 'red'
            break
            
        yield env.timeout(1)

def interceptor(env, interceptor_obj):
    target = interceptor_obj['target']
    
    while interceptor_obj['active'] and not target['hit']:
        # Calculate lead prediction
        dx = target['x'] - interceptor_obj['x']
        dy = target['y'] - interceptor_obj['y']
        distance = math.sqrt(dx**2 + dy**2)
        
        # Check if interceptor is close enough to hit
        if distance <= 500:  # Hit radius
            print(f"🚀 Intercepted {target['name']} at time {env.now} sec")
            target['color'] = 'black'
            target['hit'] = True
            interceptor_obj['active'] = False
            break
        
        # Calculate interception point with lead prediction
        target_speed = math.sqrt(target['speed_x']**2 + target['speed_y']**2)
        time_to_impact = distance / interceptor_obj['speed']
        
        # Predict where the target will be
        predicted_x = target['x'] + target['speed_x'] * time_to_impact
        predicted_y = target['y'] + target['speed_y'] * time_to_impact
        
        # Move interceptor towards predicted position
        dx_pred = predicted_x - interceptor_obj['x']
        dy_pred = predicted_y - interceptor_obj['y']
        dist_pred = math.sqrt(dx_pred**2 + dy_pred**2)
        
        if dist_pred > 0:
            # Normalize and apply speed
            vx = (dx_pred / dist_pred) * interceptor_obj['speed']
            vy = (dy_pred / dist_pred) * interceptor_obj['speed']
            
            interceptor_obj['x'] += vx
            interceptor_obj['y'] += vy
            
            # Store position for visualization
            interceptors_data.append({
                'x': interceptor_obj['x'], 
                'y': interceptor_obj['y'], 
                'color': 'orange',
                'time': env.now
            })
        
        yield env.timeout(1)
    
    interceptor_obj['active'] = False

# تشغيل البيئة
env = simpy.Environment()
for m in missiles:
    env.process(missile(env, m))

# Visualization
fig, ax = plt.subplots(figsize=(10, 10))

def update(frame):
    ax.clear()
    ax.set_xlim(-50000, 250000)
    ax.set_ylim(-50000, 300000)
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.3)
    ax.set_title(f'Missile Defense Simulation - Time: {env.now}s', fontsize=14)
    
    # Draw radar and range
    radar_circle = plt.Circle((radar_x, radar_y), radar_range, color='gray', fill=False, linestyle='--', alpha=0.5)
    ax.add_patch(radar_circle)
    ax.plot(radar_x, radar_y, 'y^', markersize=15, label='Radar')
    ax.text(radar_x, radar_y - 5000, 'Radar', ha='center', fontsize=10)
    
    # Draw missiles
    for m in missiles:
        if m['y'] > 0:  # Only show if above ground
            ax.plot(m['x'], m['y'], 'o', color=m['color'], markersize=12, alpha=0.8)
            ax.text(m['x'] + 3000, m['y'] + 3000, m['name'], fontsize=9)
            
            # Draw missile trail
            trail_x = [m['x'] + i * m['speed_x'] for i in range(-5, 1)]
            trail_y = [m['y'] + i * m['speed_y'] for i in range(-5, 1)]
            ax.plot(trail_x, trail_y, '--', color=m['color'], alpha=0.3)
            
            if m['hit']:
                ax.text(m['x'], m['y'] - 5000, "INTERCEPTED!", fontsize=12, color="red", weight="bold", ha='center')
    
    # Draw active interceptors
    for i in active_interceptors:
        if i['active']:
            ax.plot(i['x'], i['y'], 'r*', markersize=10)
            
            # Draw line to target
            if not i['target']['hit']:
                ax.plot([i['x'], i['target']['x']], [i['y'], i['target']['y']], 
                       'r--', alpha=0.3, linewidth=1)
    
    # Draw interceptor trails
    recent_trails = [i for i in interceptors_data if env.now - i['time'] < 10]
    if recent_trails:
        trail_x = [i['x'] for i in recent_trails]
        trail_y = [i['y'] for i in recent_trails]
        ax.plot(trail_x, trail_y, 'r.', markersize=3, alpha=0.5)
    
    # Add legend
    ax.legend(loc='upper right')
    
    # Step the simulation
    try:
        env.run(until=env.now + 1)
    except simpy.core.EmptySchedule:
        pass

ani = animation.FuncAnimation(fig, update, frames=400, interval=50, repeat=False)
plt.show()