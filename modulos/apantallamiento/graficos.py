import os, io
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

def generar(h, n, d, s, S, output_path):
    if S is None:
        S = 5.0
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection='3d')

    L = h * 3
    y_pts = np.linspace(-L/2, L/2, 100)
    x_pts = np.linspace(-L/2, L/2, 100)
    X, Y = np.meshgrid(x_pts, y_pts)
    Z = np.sqrt(max(0, S**2 - X**2 - Y**2))
    mask = X**2 + Y**2 <= S**2
    Z[~mask] = np.nan
    ax.plot_wireframe(X, Y, Z, alpha=0.3, color='orange', linewidth=0.5, label=f'Esfera S={S:.1f}m')

    ax.plot([-L/2, L/2], [0, 0], [0, 0], 'b-', lw=2, label='Conductor')
    ax.plot([-L/2, -L/2], [0, 0], [0, -h], 'k-', lw=2)
    ax.plot([L/2, L/2], [0, 0], [0, -h], 'k-', lw=2)

    ax.set_xlabel('X (m)'); ax.set_ylabel('Y (m)'); ax.set_zlabel('Z (m)')
    ax.set_title(f'Apantallamiento - Esfera Rodante S={S:.1f}m')
    ax.legend(loc='upper right')
    ax.view_init(elev=20, azim=-45)
    plt.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches='tight')
    plt.close(fig)
