import openai
from openai import OpenAI
import numpy as np
import streamlit as st
from typing import List, Dict

EMBED_MODEL = "text-embedding-3-small"
client = OpenAI(api_key="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")

# 1) Your 10 archetypes (goal + months + week) without the ending "in 90 days."
EXAMPLES: List[Dict] = [
    {
        "category": "realistic chill startup",
        "goal": "Launch an goal productivity app and get 1,000 early users",
        "months": [
            "Must get [MVP](https://www.reddit.com/r/startups/comments/yb5i2p/how_much_is_required_of_a_mobile_app_mvp/) up, forget about design pls",
            "Get people to use app while adding on miserable backend",
            "Pinch out best feature, improve it and add user landing",
        ],
        "weeks": [
            "Describe painful use case, otherwise ditch and find new topic",
            "Make the main.js and write [product specs](https://www.topdevelopers.co/blog/writing-specifications-for-mobile-app-development-project/)",
            "Use claude.ai to code 3+ featues",
            "Just deploy and test, [vercel](https://vercel.com/) for web",
            "Soft launch means ask friends to test",
            "Remember target audience? get 5 interviews (text counts)",
            "Ship v1.1 (yes) from top 3 complaints",
            "Maybe landing page now, ask for shares!",
            "[Pay for user boost](applovin.com), to identify best feature",
            "Improve that feature, and advertise it in X/Reddit",
            "Measure refferals and hire audit dev",
            "Test more use cases, time to make the break",
        ],
    },
    {
        "category": "muscleman fitness",
        "goal": "Gain 10 lbs of lean mass at the Gym",
        "months": [
            "Stick to a beginner plan for barley 30 days",
            "Volume block; sleep and hydration discipline",
            "Refine weak points; choose mini-cut or clean bulk",
        ],
        "weeks": [
            "Use [calorie calculator](https://www.calculator.net/calorie-calculator.html) and plan 4 day split",
            "Basic PPL schedule (12 exercises max)",
            "serious lifting = track weights",
            "Get ready to surplus, don't change lifts",
            "Surplus +300 kcal, whey protein",
            "Focus on weakest muscle group (usually legs)",
            "Focus on form, 4/5 days (one for cardio)",
            "Ensure weight is up 5-8 lbs, more carbs",
            "Assess gains and change 1 to 2 lifts",
            "Maintain, target is +15 lbs for curls",
            "Cut -200 kcal, lift weights stay same",
            "Finalize body weight, good luck",
        ],
    },
    {
        "category": "trendy investments",
        "goal": "Build a crypto investing portfolio for positions and leverage trading",
        "months": [
            "Learn with basic portfolio and with paper trade experiments",
            "Volume block, track bad habits, analyze daily [socials](https://www.reddit.com/r/CryptoCurrency/)",
            "Refine weakspots and strict strategy, track wins",
        ],
        "weeks": [
            "Open Binance + [TradingView paper trading](https://www.tradingview.com/paper-trading/), place 3 demo trades",
            "$500 split in *solid coins ETH/SOL and use [Excel journal](https://youtu.be/RLO1d-yjlV4?si=zH_Sd4M0pHCJSNiX)",
            "Set short/long strategy and note portolio moves",
            "put down at least 20+ trades this week",
            "[Notion template](https://www.notion.so/templates/crypto-tracker)",
            "Start reading [CryptoCurrency Reddit](https://www.reddit.com/r/CryptoCurrency/) daily to inspire",
            "write specific rules by recording mistakes + reddit forum",
            "setups are cool, like Glassnode [chart read](https://studio.glassnode.com/)",
            "5-bad-moves/past-30-moves and post about it",
            "cap risk at fixed %, learn more strategies",
            "restock $ for last time for risk positive moves",
            "Summarize 90-day cycle, post suggestions on [wallstreet reddit](https://www.reddit.com/r/wallstreetbets/)"
        ],
    },
    {
        #TITLES UP FOR WORK
        "category": "writing and media",
        "goal": "Grow a startup newsletter for 1000 target college students",
        "months": [
            "",
            "Launch first issues, iterate content, grow subscribers",
            "Scale distribution, deepen engagement, hit 1000 goal",
        ],
        "weeks": [
            "Create Google Form to collect 50 interest response",
            "DM 20 students on Reddit college subs asking for feedback on newsletter idea",
            "Compile 100+ student emails into Airtable CRM with tags by interest",
            "Build newsletter template in Beehiiv and draft first 3 sample issues",

            "Send issue #1 to 100 students, include 2 polls using Typeform",
            "Manually message 30 students after reading issue #1 to ask “What sucked?” and log notes",
            "Grow list to 300 by trading shoutouts with 2 student clubs on Instagram",
            "Quantitatively track open/clickthru rates in Beehiiv, set benchmark target: 35(%) open, 10(%) click",

            "Run small referral drive: “Invite 3 friends = Starbucks gift card” and track signups in Zapier",
            "Host 1-hour Zoom call with 15 readers to co-create newsletter content themes",
            "Automate weekly sending + backup list storage in GitHub repo",
            "Push to 1000 signups by cross-promoting in 5 Discord student servers with custom pitch"
        ],
    },
    {
        "category": "social media and trends",
        "goal": "Get 50k followers on my clothing brand tiktok account",
        "months": [
            "Look for brand demand and entry points to narrow down market",
            "No shortcuts, daily posting and brand expansion with Audience",
            "Paid boosts and push to 50k followers and 500 sales",
        ],
        "weeks": [
            "have brand rights, shopify, stock, and tedious stuff [all set up](https://www.shopify.com/blog/206934729-how-to-start-a-clothing-line)"
            "Catalog 150 trending fashion TikToks tag and [sounds](https://ads.tiktok.com/business/creativecenter/inspiration/popular/music/) in spreadsheet"
            "Batch film 15 outfit videos with 5 different hooks and don't delay posting"
            "[Survey](https://www.canva.com/create/surveys/) small creators on TikTok/Instagram until at least 1 unpaid collab"

            "Run TikTok poll, make fan directed content, log engagement numbers"
            "Record 2 street/online omegle interviews for outfits and upload with *pro editing"
            "Send 25 clothing pieces to micro-influencers, repost with logo overlays"
            "Dm creators and audience for real feedback, meta-post on this experience"
            
            "Audit 30 top clips in [Airtable](https://airtable.com/templates), tag hook/sound/retention patterns"
            "Consider $300 TikTok ads across 3+ posts, defintely track CPM/CTR [results](https://lebesgue.io/tiktok-ads/tiktok-ads-benchmarks-for-ctr-cr-and-cpm)"
            "Pivot content based on current results (eg. funny content is great funnel)"
            "Solidify direction and cross-platform share like Discord groups, [subreddits](https://www.reddit.com/r/DigitalMarketing/)"
        ],
    },
]

@st.cache_data
def get_embeddings(text_list):
    """
    Takes in a list of texts (goal statements),
    returns a numpy array of embeddings.
    """
    response = client.embeddings.create(
        model=EMBED_MODEL,
        input=text_list
    )
    return np.array([item.embedding for item in response.data])


# ------------------------------
# Cosine similarity helper
# ------------------------------
def cosine_similarity(vec_a, vec_b):
    """
    Simple cosine similarity:
    score = (a · b) / (||a|| * ||b||)
    """
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


# ------------------------------
# Example selector with debug
# ------------------------------
def pick_best_example(user_goal):
    # Build embeddings for examples + user input
    example_goals = [ex["goal"] for ex in EXAMPLES]
    all_texts = [user_goal] + example_goals

    vectors = get_embeddings(all_texts)
    user_vec = vectors[0]          # first = user
    example_vecs = vectors[1:]     # rest = examples

    # Calculate similarity scores
    scores = [cosine_similarity(user_vec, v) for v in example_vecs]

    # Sort by score, highest first
    ranked = sorted(zip(example_goals, scores), key=lambda x: x[1], reverse=True)

    # Debug display
    best_goal, best_score = ranked[0]
    next_goal, next_score = ranked[1]

    st.write("🔍 **Embedding Debug**")
    st.write(f"Number of Examples: {len(example_goals)}")
    st.write(f"User goal: {user_goal}")
    st.write(f"Best match → {best_goal} (score: {best_score:.3f})")
    st.write(f"Next best → {next_goal} (score: {next_score:.3f})")

    # Return best example dict
    return next(ex for ex in EXAMPLES if ex["goal"] == best_goal)

structure_dictionary = {
    "Planning → Execution → Iterate": """* Specific montly structure:
    - Month 1: Planning and trial
    - Month 2: Brutaland specific execution
    - Month 3: Evaluate and iterate on better parts of work""",
    "Specific Action + Reflect ×3": """* Specific montly structure:
    - Month 1: (Ditch all planning-based language): Weirdly hyperspecific action first three weeks and a clear reflection for last week to specific to that weird action
    - Month 2: Different hyperspecific action with the same exact shocking pattern (action -> toppling reflection)
    - Month 3: Another interesting hyperspecific action with the same exact shocking pattern (action -> toppling reflection)""",
    "Explore → Exploit → Expand": """* Specific montly structure:
    - Month 1: Unique and structured exploration of super goal (specific methods, objectives, audience)
    - Month 2: Highly leverage intial knowledge and resources to take specific actions
    - Month 3: Expand from these actions for better apporahc, then final narrowing executions on last 2 weeks""",
    "Crack Mode": """* Crazy mode on. For each month, Generate HYPERSPECIFIC targets. \
    The core strategy is making bold inferences of actions or articles (physical or digital) relevant to the goal. \
    The farther you go, the better because when you are incorrect it inspires me to correct course and take a self-determined action \
    - Month 1: Slice open a target so hard it seems impossible.
    - Month 2: Assume I've gotten ahead, now it's all a brutal numbers game
    - Month 3: Blow my goals away with hyperscaled completion, metrics, and outreach
    * Week milestones must have same brutal concision, don't worry about intepretation (if numbers and actions are there)"""
}

# 3) Build the GPT prompt
def test_prompt(test_goal: str, test_profile="", test_structure=""):
    example = pick_best_example(test_goal)

    example_months = "\n".join(
        [f"Month {i+1} Action: {m}" for i, m in enumerate(example["months"])]
    )
    example_weeks = "\n".join(
        [f"Week {i+1} Milestone: {w}" for i, w in enumerate(example["weeks"])]
    )

    # Fixed: Corrected the variable order in the example output
    return f"""
        My current Super Goal is {test_goal} in 90 days. \
        Please help me break down this goal into a strict 90-day plan with distinct and specific steps.
        {test_profile}

        ### Required Final Output
        *Generate 3 Monthly Actions. Format the output ONLY as follows, with each action on a new line*

        Month 1 Action: Action text for Month 1...
        Month 2 Action: Action text for Month 2...
        Month 3 Action: Action text for Month 3...

        *Then, Generate 12 Weekly Milestones (4 for each Month in order). Format the output ONLY as follows, with each milestone on a new line*

        Week 1 Milestone: Milestone text for Week 1...
        Week 2 Milestone: Milestone text for Week 2...
        Week 3 Milestone: Milestone text for Week 3...
        Week 4 Milestone: Milestone text for Week 4...

        Week 5 Milestone: Milestone text for Week 5...
        Week 6 Milestone: Milestone text for Week 6...
        Week 7 Milestone: Milestone text for Week 7...
        Week 8 Milestone: Milestone text for Week 8...

        Week 9 Milestone: Milestone text for Week 9...
        Week 10 Milestone: Milestone text for Week 10...
        Week 11 Milestone: Milestone text for Week 11...
        Week 12 Milestone: Milestone text for Week 12...

        ### Examples from the past
        Example super goal: {example["goal"]}
        Example 3 monthly actions:
        {example_months}
        Example 12 Weekly milestones:
        {example_weeks}

        ### Deeper Output Guidelines
        * Monthly actions must be concise with 4 to 7 keywords.
        {test_structure}
        * Week milestones break down the 3 Monthly actions and flow logically:
            - Weeks 1 to 4 support Month 1 Action
            - Weeks 5 to 8 support Month 2 Action
            - Weeks 9 to 12 support Month 3 Action
        * Specific Instructions for generating weekly milestones under each Month group:
            - Each milestone must be achievable within one week and be distinct from other milestones
            - Each weekly milestone must be hyperspecific and target the exact action with the concise context (location, platform, tool, or people)
            - Choose two weeks to be quantitative, almost like programming a robot.
            - Choose two weeks to be boldly prescriptive and uncomfortably specific to break the ice for me
            - After writing down each milestone, ensure it follows the specificity standards
            - Never use generalities like "define target audience." Instead, use statements like Turn X poll into 10-pro interview
        * The bottom line is to follow each item listed in the Required Output with zero tolerance for off-topic discussions.

        
        *Adding hyperlinks to week milestones titles
            - Identify keywords and verbs fitting (e.g., "X program”, "test X criteria", "X people community"):
            - Use clear and relevant hyperlinks for these keywords reddit.com posts for niche pursuits, github.com projects for coding, etc.
            - Always render hyperlinks as [descriptive text](url) in Markdown style, as demostrated in the complete example
            - Ensure the url starts with https://
            - Do not overload all weekly milestone with links, use a max of 6 link embedded milestones"""