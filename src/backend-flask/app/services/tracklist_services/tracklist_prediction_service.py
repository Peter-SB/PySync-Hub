from __future__ import annotations

from typing import Any
from dataclasses import dataclass
from app.models import Track, Tracklist, TracklistEntry
import app.utils.feature_scoring_utils as feature_scoring_utils


@dataclass
class FeatureScores:
    global_token_set: float         # 0 to 100 
    artist_set: float               # 0 to 100
    title_sort: float               # 0 to 100
    remix_crosscheck: float         # 0 to 100
    vip_conflict: int               # 0 or 1
    structural_conf: float          # 0 to 1.0
    length_similarity: float        # 0 to 1.0

    @classmethod
    def to_vector(cls, scores: 'FeatureScores') -> list[float | int]:
        return [
            scores.global_token_set,
            scores.artist_set,
            scores.title_sort,
            scores.remix_crosscheck,
            scores.vip_conflict,
            scores.structural_conf,
            scores.length_similarity,
        ]


class TracklistPredictionService:
    """ Service for feature scoring, string matching, and prediction. """

    @staticmethod
    def predict_tracklist_matches(tracklist: Tracklist, database_tracks: list[Track], skip_confirmed: bool = True) -> Tracklist:
        """ Predict matches for all TracklistEntry in a Tracklist. """
        for tracklist_entry in tracklist.tracklist_entries:
            if skip_confirmed and tracklist_entry.confirmed_track_id:
                continue
            TracklistPredictionService.predict_tracklist_entry_match(tracklist_entry, database_tracks)
        return tracklist


    @staticmethod
    def predict_tracklist_entry_match(tracklist_entry: TracklistEntry, database_tracks: list[Track]) -> TracklistEntry:
        """ Predict matches and populate the TracklistEntry with predicted tracks and confidence scores. """
        top_candidates = TracklistPredictionService.find_top_track_matches(tracklist_entry, database_tracks, top_n=5)

        if not top_candidates or len(top_candidates) == 0:
            print(f"No candidates found for tracklist entry {tracklist_entry.artist} - {tracklist_entry.full_title}")
            return tracklist_entry

        top_candidate, top_candidate_score = top_candidates[0]

        if top_candidate_score < 0.1:
            tracklist_entry.predicted_track_id = None
            tracklist_entry.predicted_track_confidence = None
            tracklist_entry.predicted_tracks = []
            return tracklist_entry

        tracklist_entry.predicted_tracks = top_candidates
        tracklist_entry.predicted_track_id = top_candidate.id
        tracklist_entry.predicted_track_confidence = top_candidate_score

        return tracklist_entry


    @staticmethod
    def find_top_track_matches(tracklist_entry: TracklistEntry, database_tracks: list[Track], top_n: int = 5, min_score: float = 0.0) -> list[tuple[Track, float]]:
        """ Find top N matching tracks from the database for a given import track. """
        scored_tracks = []
        for db_track in database_tracks:
            feature_scores = FeatureScores(**feature_scoring_utils.calculate_feature_scores_tracks(tracklist_entry, db_track))
            prediction = TracklistPredictionService.predict(feature_scores)
            scored_tracks.append((db_track, prediction))
        
        # Sort by prediction score descending
        scored_tracks.sort(key=lambda x: x[1], reverse=True)
        
        return [track for track in scored_tracks if track[1] >= min_score][:top_n]


    @staticmethod
    def predict(feature_scores: FeatureScores) -> float:
        """
        Predict a match score given feature scores using logistic regression.

        Returns a float confidence score between 0.0 and 1.0. >= 0.5 indicates a match.
        """
        import numpy as np
        # Coefficients and intercept from model
        weights = np.array([0.12109217, 0.00756299, 0.03052661, 0.04648941, -2.92201963, 0.46852412, 0.34230782])
        intercept = -17.97546162
        # Convert feature scores to vector
        x = np.array(FeatureScores.to_vector(feature_scores), dtype=float)
        # Linear combination
        z = np.dot(weights, x) + intercept
        # Logistic sigmoid
        score = 1 / (1 + np.exp(-z))
        return float(score)
