from langchain.agents.chat.prompt import HUMAN_MESSAGE
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from langgraph.graph import StateGraph, END
from langchain_core.runnables import RunnableLambda
import json
import os
from langchain_openai import ChatOpenAI

# === Load Traits and Conversation Flow Definitions ===
with open("traits.json") as f:
    TRAITS = json.load(f)

with open("conversation_flow.json") as f:
    FLOW = json.load(f)

# === State Object ===
class AgentState(dict):
    pass

os.environ["OPENAI_API_KEY"] = "<api key>"
client = ChatOpenAI()
# === LLM Buyer Response Generator ===
def buyer_response_fn(state: AgentState):
    messages = state["messages"]
    # Dummy LLM output for now (replace with actual LLM call)
    answer = client.invoke(messages)
    print(answer.content)
    messages.append(answer)
    return AgentState({
        **state,
        "messages": messages
    })

def init_system_prompt(state: AgentState):
    current_node = state["current_node"]
    print("state:" + current_node)
    persona = FLOW["nodes"][current_node]
    traits = [TRAITS[trait] for trait in state["traits"]]

    # Combine traits into a single behavior modifier
    trait_descriptions = "\n".join([t["behavior"] for t in traits])
    system_prompt = f"""
    
    You are a mock buyer participating in a sales coaching simulation. Respond only as the buyer. Never speak for the sales rep.
    
    Buyer State: {current_node}
    Buyer Goal: {persona["goal"]}
    Buyer Emotional state:
    {trait_descriptions}
    
    The conversation will begin when the rep greets you with an opening pitch after this prompt. 
    
    Respond as the buyer in a way consistent with the above buyer state, goal, emotional state and the rep's inputs.

    If you understand these instructions, Reply "Yes" if you understand or "No" otherwise. 

    """
    messages = state.get("messages", [])
    messages.append(SystemMessage(system_prompt))

    answer = client.invoke(messages)
    print (answer)
    state =  AgentState({
        **state,
        "rep_input": rep_input,
        "messages": messages
    })
    return state
tr

# === Transition Logic ===
def transition_logic_fn(state: AgentState):
    current_node = state["current_node"]
    for edge in FLOW["edges"]:
        if edge["from"] == current_node:
            trigger = edge["trigger"].lower()
            if triggered(trigger, state):
                print("to new state: " + edge["to"])
                return AgentState({**state, "current_node": edge["to"]})

    # No transition occurred
    return AgentState({**state})

def triggered(trigger, state):
    rep_msg = state["rep_input"]
    prompt = f"""
       You are evaluating responses from a sales rep interacting with a buyer. The rep said the following last:
       {rep_msg} 
       From the rep's last message - does it meet the following conditions:
       {trigger}
       
       Only reply "Yes" if it does or "No" otherwise.
    """

    resp = client.invoke(prompt)
    print ("************************")
    print ("end condition: " + str(resp.content))
    print ("************************")
    if "Yes" in resp.content:
        return True
    else:
        return False

def check_end_fn(state: AgentState):
    end =  state.get("current_node") != "end"
    return end

def rep_input(state: AgentState):
   rep_msg = input()
   messages = state.get("messages", [])
   messages.append(HumanMessage(rep_msg))
   state =  AgentState({
       **state,
       "rep_input": rep_msg,
       "messages": messages
   })
   return state


# === LangGraph Definition ===
graph = StateGraph(AgentState)
# Connect graph steps
graph.add_node("init", RunnableLambda(init_system_prompt))
graph.add_node("rep", RunnableLambda(rep_input))
graph.add_node("respond", RunnableLambda(buyer_response_fn))
graph.add_node("transition", RunnableLambda(transition_logic_fn))

graph.set_entry_point("init")
graph.add_edge("init", "rep")
graph.add_edge("rep", "respond")
graph.add_edge("respond", "transition")
graph.add_conditional_edges(
    "transition",
    check_end_fn,
    {True: "rep", False: END}
)

# Build the graph
app = graph.compile()

# === Example Use ===
initial_state = AgentState({
    "traits": ["money_minded", "obnoxious"],
    "current_node": "skeptical",
    "messages": []
})

result = app.invoke(initial_state)
print("\n--- Final Output ---\n", result["buyer_output"])
