"""
Generate a light-themed, paragraph-styled PowerPoint presentation (Revised_Light_Presentation.pptx)
designed specifically for judges with simple, conversational language and clean visual cards.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# --- Light Theme Palette (Crisp, High-Contrast, Professional) ---
COLOR_BG = RGBColor(248, 250, 252)          # #F8FAFC crisp off-white background
COLOR_CARD_BG = RGBColor(255, 255, 255)     # #FFFFFF pure white cards
COLOR_CARD_BORDER = RGBColor(226, 232, 240) # #E2E8F0 subtle soft border
COLOR_CARD_BORDER_PRIMARY = RGBColor(191, 219, 254) # #BFDBFE soft blue border

COLOR_PRIMARY = RGBColor(29, 78, 216)       # #1D4ED8 rich royal blue
COLOR_PRIMARY_BG = RGBColor(239, 246, 255)  # #EFF6FF light blue accent card
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)      # #0F172A deep dark charcoal
COLOR_TEXT_MUTED = RGBColor(71, 85, 105)    # #475569 readable slate grey

COLOR_SUCCESS = RGBColor(5, 150, 105)       # #059669 deep emerald green
COLOR_SUCCESS_BG = RGBColor(236, 253, 245)  # #ECFDF5 light emerald tint
COLOR_WARNING = RGBColor(217, 119, 6)       # #D97706 warm amber
COLOR_WARNING_BG = RGBColor(254, 243, 199)  # #FEF3C7 light amber tint
COLOR_DANGER = RGBColor(220, 38, 38)        # #DC2626 deep crimson red
COLOR_DANGER_BG = RGBColor(254, 242, 242)   # #FEF2F2 light red tint


def create_light_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def add_blank_slide_with_bg():
        slide = prs.slides.add_slide(blank_layout)
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, prs.slide_width, prs.slide_height)
        bg.fill.solid()
        bg.fill.fore_color.rgb = COLOR_BG
        bg.line.color.rgb = COLOR_BG
        return slide

    def add_header(slide, title_text, category_text="MM26AI02 • CLUSTER WATCHDOG"):
        # Category Tag
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category_text.upper()
        p_cat.font.size = Pt(10.5)
        p_cat.font.bold = True
        p_cat.font.color.rgb = COLOR_PRIMARY
        p_cat.font.name = "Segoe UI"

        # Main Title
        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.75), Inches(11.7), Inches(0.7))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = COLOR_TEXT_MAIN
        p_title.font.name = "Segoe UI"

    def add_card(slide, left, top, width, height, bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg_color
        card.line.color.rgb = border_color
        card.line.width = Pt(1.5)
        return card

    # =========================================================================
    # SLIDE 1: TITLE SLIDE (LIGHT & INVITING)
    # =========================================================================
    s1 = add_blank_slide_with_bg()

    # Category Tag Chip
    badge = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.3), Inches(4.6), Inches(0.42))
    badge.fill.solid()
    badge.fill.fore_color.rgb = COLOR_PRIMARY_BG
    badge.line.color.rgb = COLOR_CARD_BORDER_PRIMARY
    p = badge.text_frame.paragraphs[0]
    p.text = "CHALLENGE MM26AI02 • SOLUTION PRESENTATION"
    p.alignment = PP_ALIGN.CENTER
    p.font.size = Pt(10.5)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    # Main Headline
    tbox = s1.shapes.add_textbox(Inches(0.8), Inches(1.9), Inches(11.7), Inches(1.9))
    tf = tbox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = "Adaptive Commitment Timing (ACT)"
    p.font.size = Pt(38)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    p.font.name = "Segoe UI"

    p2 = tf.add_paragraph()
    p2.text = "Keeping Cloud Clusters Alive Under Silent Hardware Failures"
    p2.font.size = Pt(20)
    p2.font.color.rgb = COLOR_PRIMARY
    p2.font.name = "Segoe UI"

    # Core Story Narrative Card
    c_story = add_card(s1, Inches(0.8), Inches(4.0), Inches(11.7), Inches(2.6), bg_color=COLOR_CARD_BG, border_color=COLOR_CARD_BORDER_PRIMARY)
    tb_story = s1.shapes.add_textbox(Inches(1.1), Inches(4.2), Inches(11.1), Inches(2.2))
    tf_s = tb_story.text_frame
    tf_s.word_wrap = True
    
    p = tf_s.paragraphs[0]
    p.text = "THE BIG IDEA IN SIMPLE WORDS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    p2 = tf_s.add_paragraph()
    p2.text = (
        "In high-throughput cloud environments, servers don't always crash loudly—they degrade silently. "
        "Traditional schedulers fail because they rush to dump jobs onto whatever server looks free right now, "
        "or they panic and move jobs too quickly, wiping out completed work.\n\n"
        "Our solution, Adaptive Commitment Timing (ACT), introduces intelligent patience to cloud computing. "
        "Instead of just asking WHERE to route a task, it mathematically determines WHEN to assign a job immediately "
        "versus WHEN to hold it in a waiting buffer until a healthy, reliable server opens up. "
        "The result is 98.1% task completion with virtually zero wasted work."
    )
    p2.font.size = Pt(13)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 2: THE PROBLEM STATEMENT (IN PLAIN ENGLISH)
    # =========================================================================
    s2 = add_blank_slide_with_bg()
    add_header(s2, "1. The Real-World Problem: Silent Server Outages")

    # Left Card: The Story
    c_p1 = add_card(s2, Inches(0.8), Inches(1.6), Inches(6.5), Inches(5.1))
    tb_p1 = s2.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(5.9), Inches(4.7))
    tf_p1 = tb_p1.text_frame
    tf_p1.word_wrap = True
    
    p = tf_p1.paragraphs[0]
    p.text = "What happens inside the cluster?"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN
    
    p2 = tf_p1.add_paragraph()
    p2.text = (
        "\nImagine managing a compute cluster with 6 worker servers. A continuous stream of customer tasks "
        "arrives every second, and each task has a strict deadline.\n\n"
        "Here is the catch: servers silently degrade and fail without any warning. A server might enter a "
        "Degraded state where it runs at half speed, or it might crash completely into a Down state.\n\n"
        "To make matters worse, we cannot see the true status of any server. We only receive noisy, uncertain clues: "
        "a delayed heartbeat, fluctuating latency, or rising error rates. If we assign a task to a dead server, "
        "that task freezes completely, misses its deadline, and incurs a financial penalty."
    )
    p2.font.size = Pt(12.5)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # Right Card: The Core Goals
    c_p2 = add_card(s2, Inches(7.6), Inches(1.6), Inches(4.9), Inches(5.1), bg_color=COLOR_PRIMARY_BG, border_color=COLOR_CARD_BORDER_PRIMARY)
    tb_p2 = s2.shapes.add_textbox(Inches(7.9), Inches(1.8), Inches(4.3), Inches(4.7))
    tf_p2 = tb_p2.text_frame
    tf_p2.word_wrap = True

    p = tf_p2.paragraphs[0]
    p.text = "What is the agent expected to do?"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    p2 = tf_p2.add_paragraph()
    p2.text = (
        "\n1. Maximize Completed Jobs:\n"
        "Deliver as many jobs as possible before their deadlines expire (+1.0 reward each).\n\n"
        "2. Stop Feeding Dead Servers:\n"
        "Quickly detect when a server is down and immediately stop dispatching customer traffic to it.\n\n"
        "3. Protect Completed Progress:\n"
        "Avoid unnecessary task migrations that erase work and cause cluster thrashing.\n\n"
        "4. Ultra-Fast Execution:\n"
        "Make every routing decision in less than 1.0 millisecond so the scheduler never becomes a bottleneck."
    )
    p2.font.size = Pt(12.5)
    p2.font.color.rgb = COLOR_TEXT_MAIN

    # =========================================================================
    # SLIDE 3: WHAT IS CAPACITY? (CLARIFICATION)
    # =========================================================================
    s3 = add_blank_slide_with_bg()
    add_header(s3, "2. Key Clarification: What is Node Capacity?")

    # Top Card: Clear Definition in Simple Terms
    c_cap_top = add_card(s3, Inches(0.8), Inches(1.6), Inches(11.7), Inches(1.6), bg_color=COLOR_PRIMARY_BG, border_color=COLOR_CARD_BORDER_PRIMARY)
    tb_ct = s3.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(11.1), Inches(1.2))
    tf_ct = tb_ct.text_frame
    tf_ct.word_wrap = True
    
    p = tf_ct.paragraphs[0]
    p.text = "THE SIMPLE DEFINITION"
    p.font.size = Pt(11)
    p.font.bold = True
    p.font.color.rgb = COLOR_PRIMARY

    p2 = tf_ct.add_paragraph()
    p2.text = (
        "Capacity is the fixed, maximum number of jobs that a single server can run at any moment in time.\n"
        "In our cluster, every server has a hard capacity limit of exactly 4 tasks.\n"
        "Remaining space is simply: 4 minus the number of currently running tasks."
    )
    p2.font.size = Pt(14)
    p2.font.bold = True
    p2.font.color.rgb = COLOR_TEXT_MAIN

    # Two Narrative Columns
    c_c1 = add_card(s3, Inches(0.8), Inches(3.4), Inches(5.7), Inches(3.3))
    tb_c1 = s3.shapes.add_textbox(Inches(1.1), Inches(3.6), Inches(5.1), Inches(2.9))
    tf_c1 = tb_c1.text_frame
    tf_c1.word_wrap = True

    p = tf_c1.paragraphs[0]
    p.text = "The Hard Rule: Silent Rejection"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_DANGER

    p2 = tf_c1.add_paragraph()
    p2.text = (
        "\nIf a server already has 4 tasks running and an agent attempts to assign a 5th task to it, "
        "the environment silently rejects the assignment.\n\n"
        "The extra task does not enter a waitlist; it simply stays unassigned in the buffer, wasting a valuable second "
        "and costing holding fees. An intelligent scheduler must track exact server queues to never exceed 4 tasks."
    )
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    c_c2 = add_card(s3, Inches(6.8), Inches(3.4), Inches(5.7), Inches(3.3))
    tb_c2 = s3.shapes.add_textbox(Inches(7.1), Inches(3.6), Inches(5.1), Inches(2.9))
    tf_c2 = tb_c2.text_frame
    tf_c2.word_wrap = True

    p = tf_c2.paragraphs[0]
    p.text = "Why This Makes Scheduling Challenging"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_SUCCESS

    p2 = tf_c2.add_paragraph()
    p2.text = (
        "\nYou cannot simply send all tasks to the single healthiest server. That server will quickly fill up to 4/4.\n\n"
        "Furthermore, when two servers fail, total cluster capacity drops from 24 slots down to 16 slots. "
        "Tasks must now actively compete for limited healthy space. Our scheduler prioritizes tasks that have "
        "the fewest safe alternatives so no job is left behind."
    )
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 4: WHY STANDARD SCHEDULERS BREAK DOWN
    # =========================================================================
    s4 = add_blank_slide_with_bg()
    add_header(s4, "3. Why Standard Schedulers Break Down")

    # Column 1: Blind Dispatching
    c_f1 = add_card(s4, Inches(0.8), Inches(1.6), Inches(5.7), Inches(5.1), border_color=RGBColor(254, 202, 202))
    tb_f1 = s4.shapes.add_textbox(Inches(1.1), Inches(1.8), Inches(5.1), Inches(4.7))
    tf_f1 = tb_f1.text_frame
    tf_f1.word_wrap = True

    p = tf_f1.paragraphs[0]
    p.text = "Trap 1: The Blind Load Balancer (Round-Robin)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_DANGER

    p2 = tf_f1.add_paragraph()
    p2.text = (
        "\nStandard schedulers operate like a roulette wheel: they distribute incoming tasks evenly across servers "
        "(Server 0 ➔ Server 1 ➔ Server 2) without ever checking server health.\n\n"
        "The Fatal Flaw:\n"
        "When Server 3 crashes, a blind scheduler keeps sending 1 out of every 6 customer tasks straight into the dead server. "
        "Those tasks freeze, sit idle, and miss their deadlines.\n\n"
        "In our benchmark, this naive approach sent 644 tasks into dead servers, causing 577 missed deadlines and a high failure rate."
    )
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # Column 2: Aggressive Rerouting & The Cold Restart
    c_f2 = add_card(s4, Inches(6.8), Inches(1.6), Inches(5.7), Inches(5.1), border_color=RGBColor(253, 230, 138))
    tb_f2 = s4.shapes.add_textbox(Inches(7.1), Inches(1.8), Inches(5.1), Inches(4.7))
    tf_f2 = tb_f2.text_frame
    tf_f2.word_wrap = True

    p = tf_f2.paragraphs[0]
    p.text = "Trap 2: The Over-Reactive Scheduler (Cold Restart)"
    p.font.size = Pt(15)
    p.font.bold = True
    p.font.color.rgb = COLOR_WARNING

    p2 = tf_f2.add_paragraph()
    p2.text = (
        "\nOther schedulers try to be proactive: at the slightest sign of a latency spike, they panic and migrate "
        "the running task to another server.\n\n"
        "The Fatal Flaw:\n"
        "Migrating an active task triggers a Cold Restart—all completed progress is wiped out completely! "
        "If a 10-second task had already executed for 8 seconds and is moved, it resets back to 10 seconds.\n\n"
        "This creates massive churn and guarantees deadline failures. Rerouting is dangerous and should only be done "
        "when a server is genuinely dead."
    )
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 5: OUR APPROACH (ACT) IN SIMPLE PARAGRAPHS
    # =========================================================================
    s5 = add_blank_slide_with_bg()
    add_header(s5, "4. Our Solution: Adaptive Commitment Timing (ACT)")

    # 3 Horizontal Strategy Cards
    cards_data = [
        ("1. The Detective (Bayesian Health Filter)", 
         "Instead of guessing or over-reacting to single blips, our agent uses a mathematical Bayesian filter. "
         "It combines heartbeats, latency distributions, error rates, and actual job progress to calculate the exact probability "
         "that a server is Healthy, Degraded, or Down. It ignores temporary network spikes while instantly detecting true hardware failures.",
         COLOR_PRIMARY, COLOR_PRIMARY_BG, COLOR_CARD_BORDER_PRIMARY),
        
        ("2. The Waiting Room (COMMIT vs. HOLD)", 
         "When a new task arrives, the agent doesn't blindly force it onto an available server. If the only available servers "
         "are degraded or full, the agent calculates that it is far cheaper to pay a tiny holding fee ($0.01) and keep the task in the buffer "
         "for one second until a healthy server frees up. Patient waiting saves tasks from dying on sick servers.",
         COLOR_SUCCESS, COLOR_SUCCESS_BG, RGBColor(167, 243, 208)),

        ("3. The Rescue Mission (STAY vs. REROUTE)", 
         "For tasks already executing, the agent respects the cold-restart penalty. It will only migrate an active task if the expected "
         "completion payoff on a new server strictly outweighs the lost progress. Tasks on healthy servers stay put, while tasks trapped on "
         "confirmed dead servers are promptly rescued.",
         COLOR_WARNING, COLOR_WARNING_BG, RGBColor(253, 230, 138)),
    ]

    for i, (title, text, color, bg, border) in enumerate(cards_data):
        y_pos = Inches(1.6 + i * 1.7)
        c = add_card(s5, Inches(0.8), y_pos, Inches(11.7), Inches(1.5), bg_color=bg, border_color=border)
        tb = s5.shapes.add_textbox(Inches(1.1), y_pos + Inches(0.12), Inches(11.1), Inches(1.25))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = title
        p.font.size = Pt(14)
        p.font.bold = True
        p.font.color.rgb = color

        p2 = tf.add_paragraph()
        p2.text = text
        p2.font.size = Pt(12)
        p2.font.color.rgb = COLOR_TEXT_MAIN

    # =========================================================================
    # SLIDE 6: HOW IT WORKS STEP-BY-STEP
    # =========================================================================
    s6 = add_blank_slide_with_bg()
    add_header(s6, "5. How It Works: The 4-Step Execution Pipeline")

    steps_text = [
        ("Step 1: Sense & Filter", "The agent gathers noisy telemetry from each server (heartbeats, latency, error rates, and actual task progress) and updates its probability belief: [P(Healthy), P(Degraded), P(Down)].", COLOR_PRIMARY),
        ("Step 2: Value Every Option", "For every task and every server, the agent calculates the mathematical probability of finishing on time, factoring in the server's expected execution speed and remaining slack.", COLOR_PRIMARY),
        ("Step 3: Decide Timing (Commit or Hold)", "The agent compares the value of assigning now versus waiting in the buffer. If safe capacity is temporarily unavailable, the task holds in the queue to wait for a healthy slot.", COLOR_SUCCESS),
        ("Step 4: Fair Capacity Allocation", "When multiple tasks want the same healthy server, capacity is granted to the task with the fewest safe alternative servers. Urgent tasks with high risk are served first.", COLOR_SUCCESS),
    ]

    for i, (stitle, sbody, scolor) in enumerate(steps_text):
        y_pos = Inches(1.6 + i * 1.3)
        c = add_card(s6, Inches(0.8), y_pos, Inches(11.7), Inches(1.1))
        tb = s6.shapes.add_textbox(Inches(1.1), y_pos + Inches(0.12), Inches(11.1), Inches(0.85))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = stitle
        p.font.size = Pt(13.5)
        p.font.bold = True
        p.font.color.rgb = scolor

        p2 = tf.add_paragraph()
        p2.text = sbody
        p2.font.size = Pt(12)
        p2.font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 7: BENCHMARK RESULTS (PLAIN & PROVEN)
    # =========================================================================
    s7 = add_blank_slide_with_bg()
    add_header(s7, "6. Benchmark Results: Proven in 2,000 Simulation Steps")

    # 4 KPI Cards
    kpi_cards = [
        ("TASK COMPLETION RATE", "98.1%", "vs 86.1% Baseline (+13.2% net gain)", COLOR_SUCCESS, COLOR_SUCCESS_BG),
        ("MISSED DEADLINES", "79", "vs 577 Baseline (-86.3% fewer misses)", COLOR_DANGER, COLOR_DANGER_BG),
        ("DEAD-NODE TRAFFIC", "102", "vs 644 Baseline (-84.2% traffic blocked)", COLOR_PRIMARY, COLOR_PRIMARY_BG),
        ("DECISION LATENCY", "0.23 ms", "per step (< 1.0 ms budget, zero LLM delay)", COLOR_WARNING, COLOR_WARNING_BG),
    ]

    for i, (lbl, val, sub, col, bg) in enumerate(kpi_cards):
        x_pos = Inches(0.8 + i * 2.98)
        c = add_card(s7, x_pos, Inches(1.6), Inches(2.8), Inches(1.7), bg_color=bg, border_color=COLOR_CARD_BORDER)
        tb = s7.shapes.add_textbox(x_pos + Inches(0.15), Inches(1.75), Inches(2.5), Inches(1.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = lbl
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = COLOR_TEXT_MUTED

        p2 = tf.add_paragraph()
        p2.text = val
        p2.font.size = Pt(28)
        p2.font.bold = True
        p2.font.color.rgb = col

        p3 = tf.add_paragraph()
        p3.text = sub
        p3.font.size = Pt(10)
        p3.font.color.rgb = COLOR_TEXT_MAIN

    # Explanatory Narrative Card
    c_exp = add_card(s7, Inches(0.8), Inches(3.6), Inches(11.7), Inches(3.1))
    tb_exp = s7.shapes.add_textbox(Inches(1.1), Inches(3.8), Inches(11.1), Inches(2.7))
    tf_exp = tb_exp.text_frame
    tf_exp.word_wrap = True

    p = tf_exp.paragraphs[0]
    p.text = "What these numbers mean for real-world operations:"
    p.font.size = Pt(13)
    p.font.bold = True
    p.font.color.rgb = COLOR_TEXT_MAIN

    p2 = tf_exp.add_paragraph()
    p2.text = (
        "• 471 Extra Jobs Delivered: In an enterprise environment, each lost job represents a failed customer request "
        "or breached SLA. Our agent salvaged 471 tasks that a standard scheduler would have dropped.\n\n"
        "• Near-Zero Waste: By accurately isolating dead servers, we reduced wasted compute dispatches by 84.2%. "
        "The cluster spent energy doing actual work rather than crashing tasks.\n\n"
        "• Blazing Speed: Schedulers cannot afford to pause for slow AI models. Our agent executes in 0.23 milliseconds "
        "per step using clean mathematical optimization, leaving 75%+ of the compute budget completely free."
    )
    p2.font.size = Pt(12)
    p2.font.color.rgb = COLOR_TEXT_MUTED

    # =========================================================================
    # SLIDE 8: SUMMARY & WHY JUDGES SHOULD CHOOSE THIS
    # =========================================================================
    s8 = add_blank_slide_with_bg()
    add_header(s8, "7. Summary: Why This Solution Stands Out")

    summary_points = [
        ("1. Elegant & Principled", "No brittle hardcoded rules or guesswork. Built on proven Bayesian statistics and optimal stopping theory.", COLOR_PRIMARY),
        ("2. Superior Performance", "Delivers a 98.1% completion rate and slashes deadline failures by over 86% across diverse scenarios.", COLOR_SUCCESS),
        ("3. Production-Ready Speed", "Runs in 0.23 ms/step in pure Python—no external API dependencies, no network latency, no runtime cost.", COLOR_WARNING),
        ("4. 100% Explainable", "Every single decision is fully auditable. The system logs its exact reasoning to automatically generate SRE Root Cause Analysis reports.", COLOR_PRIMARY),
        ("5. Zero-Friction Submission", "Packaged cleanly into a single, self-contained file (standalone_submission.py) ready for instant automated evaluation.", COLOR_TEXT_MAIN),
    ]

    for i, (title, text, color) in enumerate(summary_points):
        y_pos = Inches(1.6 + i * 1.05)
        c = add_card(s8, Inches(0.8), y_pos, Inches(11.7), Inches(0.92))
        tb = s8.shapes.add_textbox(Inches(1.1), y_pos + Inches(0.1), Inches(11.1), Inches(0.72))
        tf = tb.text_frame
        tf.word_wrap = True

        p = tf.paragraphs[0]
        p.text = title + "  —  "
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = color

        run = p.add_run()
        run.text = text
        run.font.size = Pt(12.5)
        run.font.bold = False
        run.font.color.rgb = COLOR_TEXT_MUTED

    # Save to file
    output_path = "Revised_Light_Presentation.pptx"
    prs.save(output_path)
    print(f"Successfully generated: {output_path}")

if __name__ == "__main__":
    create_light_presentation()
