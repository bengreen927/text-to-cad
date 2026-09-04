# Grader v2 amendment

After v1 grading, the new-skill enclosure failed only the support-count check: R1 cavity corner material was counted as four extra standoffs. The protocol specifies the outside R3, but no inside corner radius. The grader already explicitly allowed square through R1 cavity corners for wall geometry; support counting contradicted that rule.

Correction: subtract the allowed wall envelope before counting material in the lower cavity. Required standoff passages, material, axes, seat and interference checks remain unchanged. Independently authored square and R1 smoke controls must both pass, and existing wrong-hole/radius/lip/seat/state controls still fail. Every unchanged candidate is rerun with v2. Initial grader, raw results and frozen hash remain in grader-v1/. No candidate model was repaired or tuned following grading.
