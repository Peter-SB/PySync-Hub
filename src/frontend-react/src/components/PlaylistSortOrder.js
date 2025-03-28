const PlaylistSortOrder = ({ sortBy, setSortBy, sortOrder, setSortOrder }) => {
    return (
        <div className="relative group inline-block text-left cursor-pointer">
            <div className="flex relative group">
                <button
                    onClick={() => setSortOrder(sortOrder === "asc" ? "desc" : "asc")}
                    className="flex items-center hover:bg-gray-200 px-2 py-2 rounded-lg"
                >
                    <img src="./icons/sorting-order.png" alt="Sort Order" className="h-6 w-6" />
                </button>
            </div>
            <div className="invisible absolute right-0 z-50 w-40 bg-white text-gray-800 rounded-lg shadow-lg border group-hover:visible">
                <div
                    onClick={() => {
                        setSortBy("created_at");
                        if (sortBy === "created_at") { setSortOrder(sortOrder === "asc" ? "desc" : "asc"); }
                    }}
                    className="px-4 py-2 hover:bg-gray-300 cursor-pointer"
                >
                    Created At
                </div>
                <div
                    onClick={() => {
                        setSortBy("last_synced");
                        if (sortBy === "last_synced") { setSortOrder(sortOrder === "asc" ? "desc" : "asc"); }
                    }}
                    className="px-4 py-2 hover:bg-gray-300 cursor-pointer"
                >
                    Last Synced
                </div>
                <div
                    onClick={() => {
                        setSortBy("name");
                        if (sortBy === "name") { setSortOrder(sortOrder === "asc" ? "desc" : "asc"); }
                    }}
                    className="px-4 py-2 hover:bg-gray-300 cursor-pointer"
                >
                    Name
                </div>
            </div>
        </div>
    );
};

export default PlaylistSortOrder;
