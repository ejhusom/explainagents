# iExplain Documentation



## Agents


- Each agent runs in its own loop until there are no more tool calls or it reaches a maximum number of iterations. This means that it can continue to work as long as it calls more tools, but when it doesn't call any more tools, or it reaches the maximum number of iterations, it will pass the context over to the next step in the workflow.