import React from 'react';
import { useDroppable } from '@dnd-kit/core';

/**
 * InsertionZone component - a droppable area for inserting a draggable item at a specific position
 * 
 * @param {string} parentId - ID of the parent container (folder or root)
 * @param {number} index - Position in the parent's children array
 * @param {object} activeDropTarget - The currently active drop target
 */
function InsertionZone({ parentId, index, activeDropTarget, indent = 0 }) {

    const droppableId = `${parentId}-insertion-${index}`;
    const { isOver, setNodeRef } = useDroppable({
        id: droppableId
    });

    const isActive =
        isOver &&
        activeDropTarget &&
        activeDropTarget.parentId === parentId &&
        activeDropTarget.index === index;

    return (
        <div
            ref={setNodeRef}
            className={`h-1 my-1 transition-colors duration-200 rounded-full ${isActive ? 'bg-blue-500' : 'bg-gray-100'}`}
            data-insertion-zone
            data-parent-id={parentId}
            data-index={index}
            style={{ // todo: switch styling to tailwind
                margin: '2px 0',
                marginLeft: `${indent * 30}px`,
            }}
        />
    );
}

export default InsertionZone;