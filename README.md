# The-Wumpus-World-Game
## Wumpus World PEAS Description

### Performance Measure
- Gold: +1000
- Death: -1000
- Per Step: -1
- Using Arrow: -10

### Environment
- 4x4 grid
- Agent starts at [1,1], facing right
- Gold and Wumpus are randomly and uniformly distributed outside of [1,1]

### Actuators
- Turn Left
- Turn Right
- Move Forward
- Grab
- Shoot Arrow

### Agent Abilities
- The agent can move forward, turn left, or turn right.
- The agent will die if it enters a square with a trap or a live Wumpus.
- Moving forward is ineffective if there is a wall in front of the agent.

### Actions
- **Grab**: Picks up an object in the square where the agent is located.
- **Shoot**: Fires an arrow in the direction the agent is facing (only one arrow available).

### Sensors
- **Smell**: The agent can smell a stench in squares directly adjacent to or containing the Wumpus.
- **Breeze**: The agent can feel a breeze in squares directly adjacent to a trap.
- **Glitter**: The agent can see a glittering light in squares containing gold.
- **Bump**: The agent feels a bump when it hits a wall.
- **Scream**: When the Wumpus is killed, it emits a scream that can be heard anywhere in the cave.
