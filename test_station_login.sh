#!/bin/bash
curl -s -X POST "http://127.0.0.1:8000/api/station/station-login" \
  -H "Content-Type: application/json" \
  -d '{"email":"suryadizhang.swe@gmail.com","password":"13Agustus!"}'
