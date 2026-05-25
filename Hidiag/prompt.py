root_classification = {

 
    # 故障分类prompt - 统一使用CloudWise格式
    "failure_cls_pod": (
        "**STRICT CLASSIFICATION RULES - NO CONTENT ANALYSIS IN RULES 1&2**\n\n"
        
        "**RULE 1: COUNT OCCURRENCES (MANDATORY FIRST CHECK)**\n"
        "Count each failure type in the 3 examples. If ANY type appears 2+ times: SELECT IT IMMEDIATELY.\n"
        "DO NOT analyze input content. DO NOT consider similarity scores.\n\n"
        
         "**RULE 2: HIGHEST SIMILARITY (IF RULE 1 FAILS)**\n"
        "If all types appear only once AND max similarity ≥ 0.5 and highest similarity similarity ≥ 0.5: HIGH confidence - directly select that type.\n"
        "DO NOT analyze input content. Trust the similarity score.\n\n"
        "**RULE 3: CONTENT ANALYSIS (ONLY IF MAX SIMILARITY < 0.50)**\n"
        "Only if all similarities < 0.50: analyze content and proportions.\n\n"
        
        "**EXAMPLES:**\n"
        "Types: [网络延迟, 网络丢包, 网络延迟] → Rule 1: 网络延迟 appears 2 times → ANSWER: 网络延迟\n"
        "Types: [进程中止, 内存负载, 读io负载], Similarities: [0.81, 0.75, 0.70] → Rule 1: all appear once → Rule 2: max 0.81 → ANSWER: 进程中止\n\n"
        
        "Failure types: k8s容器网络资源包重复发送, k8s容器网络丢包, k8s容器cpu负载, k8s容器读io负载, k8s容器网络延迟, k8s容器写io负载, k8s容器网络资源包损坏, k8s容器内存负载, k8s容器进程中止, non_failure.\n\n"
        
        "Response format: Answer: [type]   Rule [1/2/3]: [reason] "
    ),


    "failure_cls_service": (
        "You are given several examples of log metric permutations and their corresponding failure types. "
        "Based on the similarity between the current sample and the examples, infer the most likely failure_type. "
        "The failure type is selected from: k8s容器网络资源包重复发送, k8s容器网络丢包, k8s容器cpu负载, "
        "k8s容器读io负载, k8s容器网络延迟, k8s容器写io负载, k8s容器网络资源包损坏, k8s容器内存负载, "
        "k8s容器进程中止, non_failure. Think step by step and give the chain of thought.\n"
    ),

"failure_cls_node": (
    "You are given several examples of log metric permutations and their corresponding failure types. "
    "Based on the similarity between the current sample and the examples, infer the most likely failure_type. "
    "The failure type is selected from: node节点CPU故障, node 磁盘读IO消耗, node 内存消耗, "
    "node 磁盘空间消耗, node 磁盘写IO消耗, node节点CPU爬升, non_failure. \n\n"
    
    "ANALYSIS RULES:\n"
    "1. **VERY HIGH SIMILARITY (>70%)**: If any example has similarity >70%, directly choose that example's failure type\n"
    "2. **MODERATE SIMILARITY (60-70%)**: Focus on the most similar examples for decision\n"
    "3. **LOW SIMILARITY (<60%)**: Combine evidence from:\n"
    "   - Pattern matching with examples\n"
    "   - Fault type event proportions in current sample (highest proportion indicates likely failure type)\n\n"
    
    "DECISION PROCESS:\n"
    "- If max similarity >70%: Choose the failure type from the highest similarity example\n"
    "- If max similarity 60-70%: Focus on most similar examples\n"
    "- If max similarity <60%: Consider both example patterns AND fault type proportions\n\n"
    
    "Think step by step and give the chain of thought.\n"
),

   

    "failure_cls_sn": (
    "You are given several examples of log metric permutations and their corresponding failure types. "
    "Based on the similarity between the current sample and the examples, infer the most likely failure_type. "
    "The failure type is selected from: cpu_load, network_delay, network_loss, non_failure. "
   
    "\nThink step by step and give the chain of thought.\n"
),

    "failure_cls_tt": (
    "You are given several examples of log metric permutations and their corresponding failure types. "
    "Based on the similarity between the current sample and the examples, infer the most likely failure_type. "
    "The failure type is selected from: cpu_load, network_delay, network_loss, non_failure. "
  
    "\nThink step by step and give the chain of thought.\n"
),
    # 系统故障分类prompt - 统一使用CloudWise格式
 
    "fault_cls_pod": (
    "You are an experienced operator analyzing a microservice system failure. You are given:\n\n"
    "1. ENTITY DIAGNOSIS SUMMARY:\n"
    "   - Each entity's diagnosis result (failure type or non_failure)\n"
    "   - Total events count for each entity\n"
    "   - Detailed breakdown of fault-related events by type with counts and weights\n\n"
    "2. SYSTEM SUMMARY:\n"
    "   - Total number of entities and those with failures\n"
    "   - Most common fault indicators across all anomaly entities\n\n"
    "3. FAILURE PROPAGATION CONTEXT:\n"
    "   - Service dependency relationships showing potential failure propagation paths\n\n"
    "Your task is to determine the root cause fault type from: k8s容器网络资源包重复发送, k8s容器网络丢包, k8s容器cpu负载, "
    "k8s容器读io负载, k8s容器网络延迟, k8s容器写io负载, k8s容器网络资源包损坏, k8s容器内存负载, k8s容器进程中止.\n\n"
    
    "**CRITICAL DIAGNOSIS PRIORITY RULE:**\n"
    "**ALWAYS PRIORITIZE THE ENTITY DIAGNOSIS RESULT OVER INDIVIDUAL WEIGHT VALUES**\n"
    "The entity diagnosis represents the comprehensive analysis result, not just the single highest weight.\n\n"
    
    "ANALYSIS RULES:\n"
    "1. **PRIMARY RULE**: Look at the entity with most anomaly events - this entity is the epicenter of the failure\n"
    "   - **The entity diagnosis result IS the primary root cause choice**\n"
    "   - Check if the diagnosis result has substantial supporting weight (not necessarily the highest)\n"
    "   - If the diagnosis result weight ≥ 15.0: HIGH confidence - Choose the entity diagnosis directly\n"
    "   - If the diagnosis result weight ≥ 10.0: MODERATE confidence - Choose the entity diagnosis directly\n"
    "   - If the diagnosis result weight < 10.0: LOW confidence - Consider global patterns\n\n"
    
    "2. **DIAGNOSIS CONFIDENCE ASSESSMENT**: Focus on the weight of the diagnosed fault type, not the highest weight\n"
    "   - Example: If diagnosis is 'k8s容器写io负载' with weight 45.0, this is HIGH confidence\n"
    "   - Even if 'k8s容器内存负载' has weight 50.0, the diagnosis result takes priority\n"
    "   - The diagnosis represents comprehensive pattern analysis, not just event counting\n\n"
    
    "3. **SECONDARY RULE**: Only consider global patterns when diagnosis confidence is LOW\n"
    "   - Check if entity diagnosis matches the global highest fault type\n"
    "   - If they match, choose the entity diagnosis\n"
    "   - If they differ, still prefer entity diagnosis unless confidence is very low\n\n"
    
    "DECISION PROCESS:\n"
    "1. Identify the entity with most anomaly events\n"
    "2. **Get the entity diagnosis result (THIS IS YOUR PRIMARY ANSWER)**\n"
    "3. Check the weight of the diagnosed fault type (not the highest weight)\n"
    "4. If diagnosis weight ≥ 10.0: Choose the entity diagnosis directly\n"
    "5. If diagnosis weight < 10.0: Validate with global fault type statistics\n"
    "6. **Final decision: Prioritize entity diagnosis unless confidence is very low**\n\n"
    
    "EXAMPLES:\n"
    "- Entity frontend-0, diagnosis 'k8s容器写io负载' (weight: 45.0), highest weight 'k8s容器内存负载' (50.0) → Choose 'k8s容器写io负载'\n"
    "- Entity pod-3, diagnosis 'k8s容器内存负载' (weight: 8.0), highest weight 'k8s容器cpu负载' (25.0) → LOW confidence → Check global patterns\n\n"
    
    "**CRITICAL: The entity diagnosis result reflects comprehensive failure analysis. Do not override it just because another fault type has a slightly higher weight. Focus on the diagnosed fault type's weight for confidence assessment.**\n\n"
    "Think step by step and provide clear reasoning for your decision.\n"
),
    "fault_cls_service": (
        "You are an experienced operator analyzing a microservice system failure. You are given:\n\n"
        "1. ENTITY DIAGNOSIS SUMMARY:\n"
        "   - Each entity's diagnosis result (failure type or non_failure)\n"
        "   - Total events count for each entity\n"
        "   - Detailed breakdown of fault-related events by type with counts and weights\n\n"
        "2. SYSTEM SUMMARY:\n"
        "   - Total number of entities and those with failures\n"
        "   - Most common fault indicators across all anomaly entities\n\n"
        "3. FAILURE PROPAGATION CONTEXT:\n"
        "   - Service dependency relationships showing potential failure propagation paths\n\n"
        "Your task is to determine the root cause fault type from: k8s容器网络资源包重复发送, k8s容器网络丢包, k8s容器cpu负载, "
        "k8s容器读io负载, k8s容器网络延迟, k8s容器写io负载, k8s容器网络资源包损坏, k8s容器内存负载, k8s容器进程中止.\n\n"
        "CRITICAL ANALYSIS RULES:\n"
        "1. **HIGHEST WEIGHT RULE**: The service with the highest weight for any fault type is usually the root cause\n"
        "   - Weight > 0.7 is extremely strong evidence\n"
        "   - Weight > 0.5 is very strong evidence\n"
        "   - Weight > 0.2 is strong evidence\n\n"
        "2. **CONSISTENCY RULE**: When multiple services show the same fault type, especially with high weights, that's likely the root cause\n\n"
        "3. **SERVICE-LEVEL PATTERNS**:\n"
        "   - Network issues (网络延迟, 网络丢包, 网络资源包损坏, 网络资源包重复发送) propagate between services and affect multiple downstream services\n"
        "   - Resource issues (cpu负载, 内存负载) typically concentrate in specific services with high computational demands\n"
        "   - I/O issues (读io负载, 写io负载) often appear in database or storage services\n"
        "   - Process termination (进程中止) usually indicates critical service failures\n\n"
        "4. **PROPAGATION ANALYSIS**: Consider service call chains - upstream service failures often cause downstream effects\n\n"
        "DECISION PROCESS:\n"
        "1. Find the service with the highest weight for any fault type\n"
        "2. Check if multiple services support this fault type\n"
        "3. Analyze the service dependency chain for propagation patterns\n"
        "4. Verify the diagnosis consistency across services\n"
        "5. Make your decision based on the strongest evidence and propagation logic\n\n"
        "IMPORTANT: Pay special attention to upstream services with high weights, as they are more likely to be root causes.\n\n"
        "Think step by step and provide clear reasoning for your decision.\n"
    ),
    "fault_cls_node": (
    "You are an experienced operator analyzing a microservice system failure. You are given:\n\n"
    "1. ENTITY DIAGNOSIS SUMMARY:\n"
    "   - Each entity's diagnosis result (failure type or non_failure)\n"
    "   - Total events count for each entity\n"
    "   - Detailed breakdown of fault-related events by type with counts and weights\n\n"
    "2. SYSTEM SUMMARY:\n"
    "   - Total number of entities and those with failures\n"
    "   - Most common fault indicators across all anomaly entities\n\n"
    "3. FAILURE PROPAGATION CONTEXT:\n"
    "   - Service dependency relationships showing potential failure propagation paths\n\n"
    "Your task is to determine the root cause fault type from: node节点CPU故障, node 磁盘读IO消耗, node 内存消耗, "
    "node 磁盘空间消耗, node 磁盘写IO消耗, node节点CPU爬升.\n\n"
    "CRITICAL ANALYSIS RULES:\n"
    "1. **PRIMARY RULE**: Look at the entity with most anomaly events - this entity is the epicenter of the failure\n"
    "   - The entity diagnosis result is the primary candidate for root cause\n"
    "   - Check the confidence level of this diagnosis based on its highest weight:\n"
    "     * Weight ≥ 25.0: HIGH confidence - Choose the entity diagnosis directly\n"
    "     * Weight ≥ 20.0: MODERATE-HIGH confidence - Choose the entity diagnosis directly\n"
    "     * Weight ≥ 15.0: MODERATE confidence - Consider global patterns to validate\n"
    "     * Weight < 15.0: LOW confidence - Must consider global patterns\n\n"
    "2. **SECONDARY RULE**: Only consider global patterns when primary entity diagnosis confidence is MODERATE or LOW\n"
    "   - Check if entity diagnosis matches the global highest fault type\n"
    "   - If they match, choose the entity diagnosis\n"
    "   - If they differ, weigh entity diagnosis vs global evidence\n\n"
    "DECISION PROCESS:\n"
    "1. Identify the entity with most anomaly events\n"
    "2. Get the entity diagnosis result (not necessarily the highest weight fault type)\n"
    "3. Check the highest weight in that entity to assess confidence\n"
    "4. If HIGH or MODERATE-HIGH confidence: Choose the entity diagnosis directly\n"
    "5. If MODERATE or LOW confidence: Validate with global fault type statistics\n"
    "6. Make final decision based on entity diagnosis and confidence assessment\n\n"
    "EXAMPLES:\n"
    "- Entity node-5 has most anomaly events, diagnosis 'node 磁盘空间消耗', highest weight 42.0 → HIGH confidence → Choose 'node 磁盘空间消耗'\n"
    "- Entity node-3 has most anomaly events, diagnosis 'node 内存消耗', highest weight 12.0 → LOW confidence → Check global patterns\n\n"
    "IMPORTANT: The entity with most anomaly events represents the failure source. Its diagnosis result (not highest weight fault type) should be your primary choice when confidence is sufficient.\n\n"
    "Think step by step and provide clear reasoning for your decision.\n"
),
    "fault_cls_sn": (
    "You are an experienced operator analyzing a microservice system failure. You are given:\n\n"
    "1. ENTITY DIAGNOSIS SUMMARY:\n"
    "   - Each entity's diagnosis result (failure type or non_failure)\n"
    "   - Total events count for each entity\n"
    "   - Detailed breakdown of fault-related events by type with counts and weights\n\n"
    "2. SYSTEM SUMMARY:\n"
    "   - Total number of entities and those with failures\n"
    "   - Most common fault indicators across all anomaly entities\n\n"
    "3. FAILURE PROPAGATION CONTEXT:\n"
    "   - Service dependency relationships showing potential failure propagation paths\n\n"
    "Your task is to determine the root cause fault type from: cpu_load, network_delay, network_loss.\n\n"
    "ANALYSIS GUIDELINES:\n"
    "- Focus on entities with the highest fault event weights, as they are more likely to be the root cause\n"
    "- When multiple entities show the same fault type, it suggests that type is the root cause\n"
    "- Network issues (network_delay, network_loss) typically affect multiple downstream services\n"
    "- CPU issues (cpu_load) usually concentrate in specific services with high weights\n"
    "- Consider propagation patterns - root causes often appear upstream in the call chain\n"
    "- The fault type with the highest occurrence count across anomaly entities is often the root cause\n\n"
    "DECISION PROCESS:\n"
    "1. Identify which fault type appears most frequently across anomaly entities\n"
    "2. Check which entities have the highest weights for that fault type\n"
    "3. Verify if the propagation pattern supports this conclusion\n"
    "4. Select ONE root cause fault type based on the evidence\n\n"
    "Think step by step and provide clear reasoning for your decision.\n"
),
   "fault_cls_tt": (
   "You are an experienced operator analyzing a microservice system failure. You are given:\n\n"
    "1. ENTITY DIAGNOSIS SUMMARY:\n"
    "   - Each entity's diagnosis result (failure type or non_failure)\n"
    "   - Total events count for each entity\n"
    "   - Detailed breakdown of fault-related events by type with counts and weights\n\n"
    "2. SYSTEM SUMMARY:\n"
    "   - Total number of entities and those with failures\n"
    "   - Most common fault indicators across all anomaly entities\n\n"
    "3. FAILURE PROPAGATION CONTEXT:\n"
    "   - Service dependency relationships showing potential failure propagation paths\n\n"
    "Your task is to determine the root cause fault type from: cpu_load, network_delay, network_loss.\n\n"
    "CRITICAL ANALYSIS RULES:\n"
    "1. **HIGHEST WEIGHT RULE**: The entity with the highest weight for any fault type is usually the root cause\n"
    "   - Weight > 0.6 is extremely strong evidence\n"
    "   - Weight > 0.5 is very strong evidence\n"
    "   - Weight > 0.3 is strong evidence\n\n"
    "2. **CONSISTENCY RULE**: When multiple entities show the same fault type, especially with high weights, that's likely the root cause\n\n"
    "DECISION PROCESS:\n"
    "1. Find the entity with the highest weight for any fault type\n"
    "2. Check if multiple entities support this fault type\n"
    "3. Verify the diagnosis consistency across entities\n"
    "4. Make your decision based on the strongest evidence\n\n"
    "IMPORTANT: In this case, carefully examine which entity has the highest weight and what fault type it indicates.\n\n"
    "Think step by step and provide clear reasoning for your decision.\n"
),
}


rag_ablation={
    "summary_generation":"As a experienced operator, give you the failure data of the resource entity, "
                         "please generate the failure summary precisely and no more than 50 words",

    "summary_diagnose_node":"As a experienced operator, give you the failure summary and some history samples, give one most possible failure type of the entity which is selected from 'node节点CPU故障', 'node 磁盘读IO消耗', 'node 内存消耗', 'node 磁盘空间消耗', 'node 磁盘写IO消耗', 'node节点CPU爬升'. think step by step and give the reasons",

    "summary_diagnose_pod": "As a experienced operator, give you the failure summary and some history samples, give one most possible failure type of the entity comprehensively which is selected from which is selected from  k8s容器网络资源包重复发送', 'k8s容器网络丢包', 'k8s容器cpu负载', 'k8s容器读io负载', 'k8s容器网络延迟', 'k8s容器写io负载', 'k8s容器网络资源包损坏', 'k8s容器内存负载', 'k8s容器进程中止'. think step by step and give the reasons",
    "summary_diagnose_service": "As a experienced operator, give you the failure summary and some history samples, give one most possible failure type of the entity comprehensively which is selected from which is selected from  k8s容器网络资源包重复发送', 'k8s容器网络丢包', 'k8s容器cpu负载', 'k8s容器读io负载', 'k8s容器网络延迟', 'k8s容器写io负载', 'k8s容器网络资源包损坏', 'k8s容器内存负载', 'k8s容器进程中止'. think step by step and give the reasons",
}

whole_system_ablation={
    "whole_diagnose_node":"As a experienced operator, give you the failure events in the system and some example samples which including the failure events and corresponding failure type , give the failure type of microservice system which is selected from 'node节点CPU故障', 'node 磁盘读IO消耗', 'node 内存消耗', 'node 磁盘空间消耗', 'node 磁盘写IO消耗', 'node节点CPU爬升'. think step by step and give the reasons. Output_format is: failure_type:XXX.reason:XXX. no other information.",
    "whole_diagnose_pod":"As a experienced operator, give you the failure events in the system and some  example samples which including the failure events and corresponding failure type, give the failure type of  microservice system comprehensively which is selected from which is selected from  k8s容器网络资源包重复发送', 'k8s容器网络丢包', 'k8s容器cpu负载', 'k8s容器读io负载', 'k8s容器网络延迟', 'k8s容器写io负载', 'k8s容器网络资源包损坏', 'k8s容器内存负载', 'k8s容器进程中止'.  Output_format is: failure_type:XXX.reason:XXX. no other information.",
    "whole_diagnose_service":"As a experienced operator, give you the failure events in the system and some  example samples which including the failure events and corresponding failure type, give the failure type of microservice system comprehensively which is selected from which is selected from  k8s容器网络资源包重复发送', 'k8s容器网络丢包', 'k8s容器cpu负载', 'k8s容器读io负载', 'k8s容器网络延迟', 'k8s容器写io负载', 'k8s容器网络资源包损坏', 'k8s容器内存负载', 'k8s容器进程中止'.  Output_format is: failure_type:XXX.reason:XXX no other information.",
}