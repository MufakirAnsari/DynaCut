"""
Generate publication-quality circuit diagrams for the DynaCut paper.

Produces:
  1. circuit_diagram_uncut.png — Original monolithic circuit with the partition
     boundary (red dashed line) between q2 and q3.
  2. circuit_diagram_cut.png — Partitioned circuit where ALL cross-boundary
     CNOTs are replaced with QPD Meas/Prep operations.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from qiskit import QuantumCircuit
from qiskit.circuit import Gate

N = 5  # 5-qubit example
RX_ANGLE = 1.57   # ≈ π/2
RZ_ANGLE = 0.78   # ≈ π/4


def build_layer(qc, include_cross=True):
    """Build one variational layer with optional cross-boundary gate."""
    for i in range(N):
        qc.rx(RX_ANGLE, i)
        qc.rz(RZ_ANGLE, i)
    # Intra-partition A gates
    qc.cx(0, 1)
    # Near-boundary A gate
    qc.cx(1, 2)
    # Cross-boundary gate (the one that gets cut)
    if include_cross:
        qc.cx(2, 3)
    # Intra-partition B gate
    qc.cx(3, 4)


def add_partition_line(ax, extend_right=2.0):
    """
    Draw a red dashed horizontal line between q2 and q3, with
    fragment labels placed outside the circuit area.

    Qiskit mpl coordinate system:
      q0 at y=0, q1 at y=-1, q2 at y=-2, q3 at y=-3, q4 at y=-4
    Midpoint between q2 and q3: y = -2.5
    """
    xlim = ax.get_xlim()
    y_partition = -2.5  # Between q2 (y=-2) and q3 (y=-3)

    ax.axhline(y=y_partition, color='red', linestyle='--', linewidth=2.0,
               alpha=0.85, zorder=5)

    # Extend the x-axis to make room for labels on the right
    new_xmax = xlim[1] + extend_right
    ax.set_xlim(xlim[0], new_xmax)

    # Fragment labels — placed in the extended right margin
    x_label = xlim[1] + extend_right * 0.5
    ax.text(x_label, -1.0, 'Fragment A\n$(q_0$–$q_2)$',
            fontsize=9, color='red', fontweight='bold', alpha=0.9,
            va='center', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='red', alpha=0.9, linewidth=1.5))
    ax.text(x_label, -3.5, 'Fragment B\n$(q_3$–$q_4)$',
            fontsize=9, color='red', fontweight='bold', alpha=0.9,
            va='center', ha='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                      edgecolor='red', alpha=0.9, linewidth=1.5))


# ==========================================================================
# 1. UNCUT CIRCUIT
# ==========================================================================
qc_uncut = QuantumCircuit(N)
qc_uncut.h(range(N))
qc_uncut.barrier()
build_layer(qc_uncut, include_cross=True)
qc_uncut.barrier()
build_layer(qc_uncut, include_cross=True)

fig_uncut = qc_uncut.draw(output='mpl', style='clifford', scale=0.8)
ax_uncut = fig_uncut.axes[0]
add_partition_line(ax_uncut)
ax_uncut.set_title('(a) Original Monolithic Circuit', fontsize=12,
                    fontweight='bold', pad=10)

fig_uncut.savefig('paper/figures/circuit_diagram_uncut.png', dpi=300,
                  bbox_inches='tight')
plt.close(fig_uncut)
print("Saved circuit_diagram_uncut.png")


# ==========================================================================
# 2. CUT CIRCUIT — ALL cross-boundary cx(2,3) replaced with QPD ops
# ==========================================================================
qpd_meas = Gate(name='QPD Meas', num_qubits=1, params=[])
qpd_prep = Gate(name='QPD Prep', num_qubits=1, params=[])

qc_cut = QuantumCircuit(N)
qc_cut.h(range(N))
qc_cut.barrier()

# Layer 1 — cross-boundary gate replaced
for i in range(N):
    qc_cut.rx(RX_ANGLE, i)
    qc_cut.rz(RZ_ANGLE, i)
qc_cut.cx(0, 1)
qc_cut.cx(1, 2)
qc_cut.append(qpd_meas, [2])
qc_cut.append(qpd_prep, [3])
qc_cut.cx(3, 4)

qc_cut.barrier()

# Layer 2 — cross-boundary gate replaced
for i in range(N):
    qc_cut.rx(RX_ANGLE, i)
    qc_cut.rz(RZ_ANGLE, i)
qc_cut.cx(0, 1)
qc_cut.cx(1, 2)
qc_cut.append(qpd_meas, [2])
qc_cut.append(qpd_prep, [3])
qc_cut.cx(3, 4)

fig_cut = qc_cut.draw(output='mpl', style='clifford', scale=0.8)
ax_cut = fig_cut.axes[0]
add_partition_line(ax_cut)
ax_cut.set_title('(b) Partitioned Circuit (QPD at Cut Boundaries)',
                  fontsize=12, fontweight='bold', pad=10)

fig_cut.savefig('paper/figures/circuit_diagram_cut.png', dpi=300,
                bbox_inches='tight')
plt.close(fig_cut)
print("Saved circuit_diagram_cut.png")

print("Done!")
