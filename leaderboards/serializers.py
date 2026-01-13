"""DRF serializers for leaderboards app - PLACEHOLDER"""
from rest_framework import serializers
from .models import LeaderboardEntry, RankSnapshot

class LeaderboardEntrySerializer(serializers.ModelSerializer):
    scope_display = serializers.CharField(source='get_scope_display', read_only=True)
    period_display = serializers.CharField(source='get_period_display', read_only=True)
    
    class Meta:
        model = LeaderboardEntry
        fields = ['id', 'scope', 'scope_display', 'period', 'period_display', 'rank', 'score', 'percentile']

class RankSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = RankSnapshot
        fields = ['rank_at_snapshot', 'score_at_snapshot', 'percentile_at_snapshot', 'snapshot_date']
