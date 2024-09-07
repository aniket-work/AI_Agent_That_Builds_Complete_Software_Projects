import matplotlib.pyplot as plt
import networkx as nx

# Create a directed graph
G = nx.DiGraph()

# Add nodes with labels
labels = {"A": "Start", "B": "CLI Arguments", "C": "Read Task", "D": "Read Task from File", "E": "Prompt User for Task",
          "F": "Initialize NemoAgent", "G": "Run Task", "H": "Ensure UV Installed", "I": "Create Project with UV",
          "J": "Implement Solution", "K": "Code Quality Check", "L": "Output Result", "M": "Improve Code",
          "N": "Zip Option", "O": "Create Zip File", "P": "Leave Files in Directory", "Q": "Clean Up Project Directory", "R": "End"}

G.add_edges_from([
    ("A", "B"), ("B", "C"), ("B", "D"), ("B", "E"),
    ("C", "F"), ("D", "F"), ("E", "F"), ("F", "G"),
    ("G", "H"), ("H", "I"), ("I", "J"), ("J", "K"),
    ("K", "L"), ("K", "M"), ("M", "K"), ("L", "N"),
    ("N", "O"), ("N", "P"), ("O", "Q"), ("P", "R"), ("Q", "R")
])

# Define node positions manually for better spacing
pos = {"A": (0, 5), "B": (2, 5), "C": (4, 7), "D": (4, 5), "E": (4, 3),
       "F": (6, 5), "G": (8, 5), "H": (10, 5), "I": (12, 5), "J": (14, 5),
       "K": (16, 5), "L": (18, 6), "M": (18, 4), "N": (20, 6), "O": (22, 7),
       "P": (22, 5), "Q": (24, 7), "R": (24, 5)}

# Create the figure and axis
fig, ax = plt.subplots(figsize=(20, 10))

# Draw nodes
nx.draw_networkx_nodes(G, pos, node_size=3000, node_color='lightblue', ax=ax)
nx.draw_networkx_edges(G, pos, edge_color='gray', arrows=True, ax=ax)

# Draw node labels
nx.draw_networkx_labels(G, pos, labels, font_size=8, font_weight="bold", ax=ax)

# Add edge labels with adjusted positions
edge_labels = {("B", "C"): "Task provided", ("B", "D"): "File provided", ("B", "E"): "No task or file",
               ("K", "L"): "Meets Standards", ("K", "M"): "Needs Improvement", ("N", "O"): "Yes", ("N", "P"): "No"}

for edge, label in edge_labels.items():
    x = (pos[edge[0]][0] + pos[edge[1]][0]) / 2
    y = (pos[edge[0]][1] + pos[edge[1]][1]) / 2
    ax.text(x, y, label, fontsize=8, color='red', ha='center', va='center', bbox=dict(facecolor='white', edgecolor='none', alpha=0.7))

# Remove axis
ax.axis('off')

# Adjust the layout to prevent cutoff
plt.tight_layout()

# Save the figure
plt.savefig("diagram.png", dpi=300, bbox_inches='tight')
plt.close()