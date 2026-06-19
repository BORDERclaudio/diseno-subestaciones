import os, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def catenary(x, l, f):
    a = 4 * f / l**2
    return a * x * (l - x)

def generar(l, fes, h, li, bh, ang, output_path):
    n_pts = 200
    x_pts = np.linspace(-l/2, l/2, n_pts)
    z_pts = catenary(x_pts + l/2, l, fes)
    theta = np.radians(ang)
    z_swung = z_pts * np.cos(theta)
    y_swung = z_pts * np.sin(theta)

    fig = plt.figure(figsize=(9, 6))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot(x_pts, np.zeros_like(x_pts), -z_pts, 'b-', lw=2.5, label='Conductor sin CC')
    ax.plot(x_pts, y_swung, -z_swung, 'r-', lw=2.5, label=f'Conductor con CC ({ang:.1f})')
    ax.plot([-l/2, -l/2], [0, 0], [0, -h], 'k-', lw=2)
    ax.plot([l/2, l/2], [0, 0], [0, -h], 'k-', lw=2)
    if li > 0:
        ax.plot([-l/2, -l/2+li], [0,0], [-h, -h+h*0.1], 'g-', lw=2, label='Aisladores')
        ax.plot([l/2, l/2-li], [0,0], [-h, -h+h*0.1], 'g-', lw=2)
    ax.quiver(0, 0, -fes, 0, bh, 0, color='orange', linewidth=2, label=f'bh={bh:.2f}m')
    ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)'); ax.set_zlabel('Z (m)')
    max_y = bh * 1.5 + 0.5
    ax.set_xlim(-l/2*1.2, l/2*1.2)
    ax.set_ylim(-0.5, max_y)
    ax.set_zlim(-h*1.1, 0.5)
    ax.set_title(f"Conductor flexible - Vano {l}m, Flecha {fes:.2f}m, bh={bh:.2f}m")
    ax.legend(loc='upper right')
    ax.view_init(elev=25, azim=-60)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
