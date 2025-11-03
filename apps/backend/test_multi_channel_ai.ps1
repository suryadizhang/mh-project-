# Multi-Channel AI Test Script
# Tests AI responses across different communication channels

Write-Host "🧪 Testing Multi-Channel AI System" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"

# Test Case 1: Malia's Email (Real customer inquiry)
Write-Host "📧 TEST 1: Email Inquiry (Malia's Real Email)" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow

$maliaEmail = @{
    message = @"
I'm looking into booking a hibachi experience for 9 people in August of 2026, likely in the Sonoma area. Do you have a quote I could take a look at? 

Looking forward to hearing from you.

Malia

--
Malia Nakamura

(206)-661-8822
"@
    channel = "email"
    customer_metadata = @{
        source = "contact_form"
        timestamp = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
    }
} | ConvertTo-Json -Depth 10

Write-Host "Request:" -ForegroundColor Gray
Write-Host $maliaEmail -ForegroundColor DarkGray
Write-Host ""

try {
    $startTime = Get-Date
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/process" -Method POST -Body $maliaEmail -ContentType "application/json"
    $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Response Time: $($elapsed)ms" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Extracted Information:" -ForegroundColor Yellow
    Write-Host "  - Customer: $($response.metadata.customer_name)" -ForegroundColor White
    Write-Host "  - Party Size: $($response.metadata.party_size) people" -ForegroundColor White
    Write-Host "  - Location: $($response.metadata.location)" -ForegroundColor White
    Write-Host "  - Inquiry Type: $($response.metadata.inquiry_type)" -ForegroundColor White
    Write-Host "  - Sentiment: $($response.metadata.sentiment)" -ForegroundColor White
    Write-Host "  - Estimated Quote: `$$($response.metadata.estimated_quote)" -ForegroundColor Green
    Write-Host ""
    Write-Host "🤖 AI Response:" -ForegroundColor Yellow
    Write-Host "---------------" -ForegroundColor Yellow
    Write-Host $response.response_text -ForegroundColor White
    Write-Host ""
    Write-Host "📊 AI Metadata:" -ForegroundColor Yellow
    Write-Host "  - Model: $($response.ai_metadata.model_used)" -ForegroundColor White
    Write-Host "  - Confidence: $($response.ai_metadata.confidence)" -ForegroundColor White
    Write-Host "  - Cached: $($response.ai_metadata.from_cache)" -ForegroundColor White
    Write-Host "  - Complexity: $($response.ai_metadata.complexity_score)" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Suggested Actions:" -ForegroundColor Yellow
    foreach ($action in $response.suggested_actions) {
        Write-Host "  - $action" -ForegroundColor Cyan
    }
    Write-Host ""
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test Case 2: Instagram DM (Same inquiry, different channel)
Write-Host "📱 TEST 2: Instagram DM (Casual Version)" -ForegroundColor Yellow
Write-Host "----------------------------------------" -ForegroundColor Yellow

$instagramDM = @{
    message = "hey! looking to book hibachi for 9 people in sonoma for august 2026. what's ur pricing? 🍱"
    channel = "instagram"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/process" -Method POST -Body $instagramDM -ContentType "application/json"
    $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Response Time: $($elapsed)ms" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🤖 Instagram Response:" -ForegroundColor Yellow
    Write-Host $response.response_text -ForegroundColor White
    Write-Host ""
    Write-Host "Length: $($response.response_text.Length) chars (max 1000 for Instagram)" -ForegroundColor Gray
    Write-Host "Model: $($response.ai_metadata.model_used)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test Case 3: SMS (Ultra brief)
Write-Host "💬 TEST 3: SMS Inquiry" -ForegroundColor Yellow
Write-Host "---------------------" -ForegroundColor Yellow

$sms = @{
    message = "Price for 9 ppl sonoma?"
    channel = "sms"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/process" -Method POST -Body $sms -ContentType "application/json"
    $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Response Time: $($elapsed)ms" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🤖 SMS Response:" -ForegroundColor Yellow
    Write-Host $response.response_text -ForegroundColor White
    Write-Host ""
    Write-Host "Length: $($response.response_text.Length) chars (target ≤160 for SMS)" -ForegroundColor Gray
    if ($response.response_text.Length -le 160) {
        Write-Host "✅ Fits in single SMS!" -ForegroundColor Green
    } else {
        Write-Host "⚠️ Requires multiple SMS messages" -ForegroundColor Yellow
    }
    Write-Host ""
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test Case 4: Phone Transcript (Talking points)
Write-Host "☎️ TEST 4: Phone Transcript" -ForegroundColor Yellow
Write-Host "-------------------------" -ForegroundColor Yellow

$phoneTranscript = @{
    message = "Hi, I'm calling about booking a hibachi chef for 9 people in Sonoma for next August. Can you tell me about your pricing and what's included?"
    channel = "phone_transcript"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/process" -Method POST -Body $phoneTranscript -ContentType "application/json"
    $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Response Time: $($elapsed)ms" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🤖 Phone Talking Points:" -ForegroundColor Yellow
    Write-Host $response.response_text -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test Case 5: Compare ALL channels side-by-side
Write-Host "🔍 TEST 5: Compare Responses Across All Channels" -ForegroundColor Yellow
Write-Host "------------------------------------------------" -ForegroundColor Yellow

$testMessage = @{
    message = "What payment methods do you accept?"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/test-all-channels" -Method POST -Body $testMessage -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host ""
    Write-Host "Original Question: $($response.original_message)" -ForegroundColor Cyan
    Write-Host ""
    
    foreach ($channel in $response.responses_by_channel.PSObject.Properties) {
        Write-Host "📢 $($channel.Name.ToUpper()):" -ForegroundColor Yellow
        Write-Host "  Length: $($channel.Value.length) chars" -ForegroundColor Gray
        Write-Host "  Model: $($channel.Value.model_used)" -ForegroundColor Gray
        Write-Host "  Cached: $($channel.Value.cached)" -ForegroundColor Gray
        Write-Host "  Response: $($channel.Value.response.Substring(0, [Math]::Min(100, $channel.Value.response.Length)))..." -ForegroundColor White
        Write-Host ""
    }
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

Start-Sleep -Seconds 2

# Test Case 6: Complaint (Negative sentiment)
Write-Host "⚠️ TEST 6: Complaint Handling" -ForegroundColor Yellow
Write-Host "----------------------------" -ForegroundColor Yellow

$complaint = @{
    message = "I'm very disappointed with my last booking. The chef arrived 2 hours late and the food was cold. I want a refund."
    channel = "email"
} | ConvertTo-Json

try {
    $startTime = Get-Date
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/process" -Method POST -Body $complaint -ContentType "application/json"
    $elapsed = ((Get-Date) - $startTime).TotalMilliseconds
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host "Response Time: $($elapsed)ms" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "📋 Analysis:" -ForegroundColor Yellow
    Write-Host "  - Sentiment: $($response.metadata.sentiment)" -ForegroundColor White
    Write-Host "  - Urgency: $($response.metadata.urgency)" -ForegroundColor White
    Write-Host "  - Requires Follow-up: $($response.metadata.requires_follow_up)" -ForegroundColor White
    Write-Host ""
    Write-Host "🤖 AI Response:" -ForegroundColor Yellow
    Write-Host $response.response_text -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Suggested Actions:" -ForegroundColor Yellow
    foreach ($action in $response.suggested_actions) {
        Write-Host "  - $action" -ForegroundColor Cyan
    }
    Write-Host ""
    Write-Host "📊 Model Used: $($response.ai_metadata.model_used)" -ForegroundColor Yellow
    if ($response.ai_metadata.model_used -eq "gpt-4") {
        Write-Host "✅ Correctly escalated to GPT-4 for complaint!" -ForegroundColor Green
    }
    Write-Host ""
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

# Test Case 7: Analyze Only (No response generation)
Write-Host "🔍 TEST 7: Inquiry Analysis (Extract Info Only)" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow

$analyzeRequest = @{
    message = @"
Hi there! I'm planning a birthday party for my wife and would love to book your hibachi service. We're looking at 12 guests on June 15th, 2026, somewhere in the Sacramento area. A few of our guests are vegetarian and one has a severe nut allergy. Can you accommodate this? Also, what's your cancellation policy?

Thanks,
David Chen
david.chen@email.com
(530) 555-0123
"@
    channel = "email"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/api/v1/ai/multi-channel/inquiries/analyze" -Method POST -Body $analyzeRequest -ContentType "application/json"
    
    Write-Host "✅ SUCCESS" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Extracted Information:" -ForegroundColor Yellow
    Write-Host "  - Party Size: $($response.analysis.party_size)" -ForegroundColor White
    Write-Host "  - Event Month: $($response.analysis.event_month)" -ForegroundColor White
    Write-Host "  - Event Year: $($response.analysis.event_year)" -ForegroundColor White
    Write-Host "  - Location: $($response.analysis.location)" -ForegroundColor White
    Write-Host "  - Customer: $($response.analysis.customer_name)" -ForegroundColor White
    Write-Host "  - Phone: $($response.analysis.customer_phone)" -ForegroundColor White
    Write-Host "  - Email: $($response.analysis.customer_email)" -ForegroundColor White
    Write-Host "  - Inquiry Type: $($response.analysis.inquiry_type)" -ForegroundColor White
    Write-Host "  - Sentiment: $($response.analysis.sentiment)" -ForegroundColor White
    Write-Host "  - Special Requests: $($response.analysis.special_requests -join ', ')" -ForegroundColor White
    Write-Host "  - Dietary: $($response.analysis.dietary_restrictions -join ', ')" -ForegroundColor White
    Write-Host ""
    Write-Host "🎯 Routing Recommendation:" -ForegroundColor Yellow
    Write-Host "  - Priority: $($response.routing_recommendation.priority)" -ForegroundColor White
    Write-Host "  - Human Review: $($response.routing_recommendation.requires_human_review)" -ForegroundColor White
    Write-Host "  - Suggested Model: $($response.routing_recommendation.estimated_response_model)" -ForegroundColor White
    Write-Host ""
} catch {
    Write-Host "❌ FAILED" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
}

# Summary
Write-Host "=================================" -ForegroundColor Cyan
Write-Host "🎉 Multi-Channel AI Tests Complete!" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Tested Channels:" -ForegroundColor Yellow
Write-Host "  - Email (professional, detailed)" -ForegroundColor White
Write-Host "  - Instagram DM (casual, emojis)" -ForegroundColor White
Write-Host "  - SMS (ultra brief, <160 chars)" -ForegroundColor White
Write-Host "  - Phone Transcript (talking points)" -ForegroundColor White
Write-Host "  - Facebook Messenger" -ForegroundColor White
Write-Host "  - Web Chat" -ForegroundColor White
Write-Host ""
Write-Host "✅ Features Tested:" -ForegroundColor Yellow
Write-Host "  - Information extraction (name, phone, party size, location)" -ForegroundColor White
Write-Host "  - Sentiment analysis (positive, neutral, negative)" -ForegroundColor White
Write-Host "  - Urgency detection" -ForegroundColor White
Write-Host "  - Quote calculation" -ForegroundColor White
Write-Host "  - Channel-specific formatting" -ForegroundColor White
Write-Host "  - Intelligent model routing" -ForegroundColor White
Write-Host "  - Complaint escalation" -ForegroundColor White
Write-Host ""
Write-Host "📝 Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Review AI responses for quality and accuracy" -ForegroundColor White
Write-Host "  2. Integrate with actual email/SMS/social media APIs" -ForegroundColor White
Write-Host "  3. Set up automated response workflows" -ForegroundColor White
Write-Host "  4. Train staff on suggested actions" -ForegroundColor White
Write-Host ""
