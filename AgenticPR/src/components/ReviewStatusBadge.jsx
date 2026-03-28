/**
 * ReviewStatusBadge — Visual indicator for review pipeline status.
 *
 * Shows the current review stage with animated progress indicator,
 * color-coded status, and elapsed time. Integrates with SSE for
 * realtime updates.
 *
 * Usage:
 *   <ReviewStatusBadge jobId={42} status="reviewing" />
 *   <ReviewStatusBadge jobId={42} />  // uses SSE for live updates
 */

import React, { useMemo } from 'react';
import { useReviewStream, STATUS_CONFIG, isTerminalStatus, isActiveStatus } from '../hooks/useReviewStream';
import './ReviewStatusBadge.css';


/**
 * Animated pipeline progress visualizer.
 */
const STAGES = ['queued', 'fetching', 'analyzing', 'reviewing', 'publishing', 'completed'];

export function ReviewStatusBadge({ jobId, status: externalStatus, showStages = false, compact = false }) {
  const { status: sseStatus, stage, isLive } = useReviewStream(jobId);
  
  // Prefer SSE status if live, otherwise fall back to external status
  const currentStatus = sseStatus || externalStatus || 'queued';
  const config = STATUS_CONFIG[currentStatus] || STATUS_CONFIG.queued;
  
  const currentStageIndex = useMemo(() => {
    return STAGES.indexOf(currentStatus);
  }, [currentStatus]);

  if (compact) {
    return (
      <span className={`review-badge review-badge--compact ${config.bg}`}>
        <span className="review-badge__icon">{config.icon}</span>
        <span className={`review-badge__label ${config.color}`}>{config.label}</span>
        {isLive && isActiveStatus(currentStatus) && (
          <span className="review-badge__pulse" />
        )}
      </span>
    );
  }

  return (
    <div className={`review-badge ${config.bg}`}>
      <div className="review-badge__header">
        <span className="review-badge__icon">{config.icon}</span>
        <span className={`review-badge__label ${config.color}`}>{config.label}</span>
        {isLive && isActiveStatus(currentStatus) && (
          <span className="review-badge__pulse" />
        )}
      </div>
      
      {showStages && !isTerminalStatus(currentStatus) && (
        <div className="review-badge__stages">
          {STAGES.slice(0, -1).map((stageName, i) => {
            let stageState = 'pending';
            if (i < currentStageIndex) stageState = 'done';
            else if (i === currentStageIndex) stageState = 'active';
            
            return (
              <div key={stageName} className={`review-badge__stage review-badge__stage--${stageState}`}>
                <div className="review-badge__stage-dot" />
                <span className="review-badge__stage-label">
                  {stageName.charAt(0).toUpperCase() + stageName.slice(1)}
                </span>
              </div>
            );
          })}
          <div className="review-badge__stage-line" />
        </div>
      )}
    </div>
  );
}


/**
 * Full pipeline progress bar for detail views.
 */
export function ReviewPipelineProgress({ jobId, status: externalStatus }) {
  const { status: sseStatus, events } = useReviewStream(jobId);
  const currentStatus = sseStatus || externalStatus || 'queued';
  const currentStageIndex = STAGES.indexOf(currentStatus);
  const progress = isTerminalStatus(currentStatus) 
    ? 100 
    : Math.max(0, (currentStageIndex / (STAGES.length - 1)) * 100);

  return (
    <div className="review-pipeline">
      {/* Progress bar */}
      <div className="review-pipeline__bar">
        <div 
          className={`review-pipeline__fill ${
            currentStatus === 'failed' ? 'review-pipeline__fill--failed' :
            currentStatus === 'completed' ? 'review-pipeline__fill--done' :
            'review-pipeline__fill--active'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>
      
      {/* Stage dots */}
      <div className="review-pipeline__dots">
        {STAGES.map((stageName, i) => {
          let dotClass = 'review-pipeline__dot';
          if (i < currentStageIndex || isTerminalStatus(currentStatus)) {
            dotClass += ' review-pipeline__dot--done';
          } else if (i === currentStageIndex && isActiveStatus(currentStatus)) {
            dotClass += ' review-pipeline__dot--active';
          }
          
          return (
            <div key={stageName} className={dotClass}>
              <div className="review-pipeline__dot-inner" />
              <span className="review-pipeline__dot-label">
                {stageName === 'queued' ? 'Queue' :
                 stageName === 'fetching' ? 'Fetch' :
                 stageName === 'analyzing' ? 'Analyze' :
                 stageName === 'reviewing' ? 'Review' :
                 stageName === 'publishing' ? 'Publish' :
                 'Done'}
              </span>
            </div>
          );
        })}
      </div>
      
      {/* Event log (last 5) */}
      {events.length > 0 && (
        <div className="review-pipeline__log">
          {events.slice(-5).map((evt, i) => (
            <div key={i} className="review-pipeline__log-entry">
              <span className="review-pipeline__log-time">
                {new Date(evt.timestamp * 1000).toLocaleTimeString()}
              </span>
              <span className="review-pipeline__log-msg">
                {evt.event.replace(/_/g, ' ')}
                {evt.duration_ms ? ` (${(evt.duration_ms / 1000).toFixed(1)}s)` : ''}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}


export default ReviewStatusBadge;
