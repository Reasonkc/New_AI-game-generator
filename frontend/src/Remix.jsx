import React from "react";
import { useParams, Link } from "react-router";
import { useState, useEffect } from "react";

const GAME_BOOK_OBJECT_ID =
    "0x6beae9325f296d0978e0d26c2277f204923e8e83472e3f60b713b8e334e942e2";
const AI_GAME_GENERATOR_PACKAGE_ID =
    "0x7b1f0507ef23d66e600f77e8209f52a864e117719ac017604ee8327a2d3c55e9";
const NETWORK = "testnet"; // or "mainnet" for production
const FULLNODE_URL = "https://fullnode.testnet.sui.io"; // or your custom fullnode URL


const Remix = () => {
    return(<></>)
    const [gameHtml, setGameHtml] = useState(null);
    const [game, setGame] = useState(null);
    const [games, setGames] = useState(() => {
        const saved = localStorage.getItem("games");
        return saved ? JSON.parse(saved) : [];
    });
    const [loading, setLoading] = useState(false);
    const { gameId } = useParams();
    const [feedbackPrompt, setFeedbackPrompt] = useState("");
    const [showMintForm, setShowMintForm] = useState(false);
    const [creatorName, setCreatorName] = useState("");
    const [title, setTitle] = useState("");
    const [error, setError] = useState(null);
    const [txnDigest, setTxnDigest] = useState(null);
    const [blobId, setBlobId] = useState(null);
    const [imageBlobId, setImageBlobId] = useState(null);
    const [parent, setParent] = useState(0);
    const [price, setPrice] = useState(0);
    const { isLoggedIn, login, logout, userDetails } = useLogin();
    const flow = useEnokiFlow();
    useEffect(() => {
        setParent(parseInt(gameId, 10));
        const foundGame = games.find((g) => g.game_id === gameId);
        setGame(foundGame);
    }, [games, gameId]);

    useEffect(() => {
        const fetchGameHtml = async () => {
            if (!game?.blob_id) return;
            try {
                const blobId = game.blob_id;
                const decoder = new TextDecoder();
                const blob_id_decoded = decoder.decode(new Uint8Array(blobId));
                const response = await fetch(
                    `http://127.0.1:5000/get_blob/${blob_id_decoded}`
                );
                if (!response.ok) throw new Error("Game not found");
                const data = await response.text();
                setGameHtml(data);
            } catch (err) {
                console.error(err);
                setError("Failed to load game HTML.");
            }
        };

        fetchGameHtml();
    }, [game]);

    const store_blob = async () => {
        if (!gameHtml) return;

        try {
            const response = await fetch("http://127.0.1:5000/store_blob", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ gameHtml: gameHtml }),
            });
            if (response.ok) {
                const data = await response.json();
                console.log(data);
                setBlobId(data.blob_id);
                setImageBlobId(data.image_blob_id);
                return data; // Return the data so we can use it directly
            } else {
                const errorText = await response.text();
                console.error("Backend error:", errorText);
                throw new Error(errorText);
            }
        } catch (err) {
            setError("Failed to get blob. Please try again.");
            throw err;
        }
    };

    const handleShowMintForm = () => {
        setShowMintForm(true);
    };

    const handleMint = async () => {
        if (!creatorName.trim()) {
            setError("Creator name is required.");
            return;
        }

        try {
            setLoading(true);
            const blobData = await store_blob();
            console.log("Blob ID:", blobData.blob_id);
            console.log("Image Blob ID:", blobData.image_blob_id);
            await handleCreateGame(blobData.blob_id, blobData.image_blob_id);
        } catch (err) {
            setError("Failed to mint game. Please try again.");
            console.error("Error:", err);
        } finally {
            setLoading(false);
        }
    };
    const handleCreateGame = async (blob_id, image_blob_id) => {
        if (!userDetails) {
            setError("Please log in first.");
            return;
        }
        if (!flow) {
            setError("Enoki Flow not available.");
            return;
        }

        setTxnDigest(null);
        setError(null);

        try {
            console.log(`Using network: ${NETWORK} (${FULLNODE_URL})`);
            const suiClient = new SuiClient({ url: FULLNODE_URL });
            const keypair = await flow.getKeypair({ network: NETWORK });

            console.log("User Address:", keypair.getPublicKey().toSuiAddress());
            console.log("GameBook Object ID:", GAME_BOOK_OBJECT_ID);

            const txb = new Transaction();

            // Convert strings to `vector<u8>`
            const blobBytes = new TextEncoder().encode(blob_id);
            const imageBlobBytes = new TextEncoder().encode(image_blob_id);

            // Encode each one using BCS
            const blobBytesBCS = bcs
                .vector(bcs.u8())
                .serialize(Array.from(blobBytes))
                .toBytes();
            const imageBlobBytesBCS = bcs
                .vector(bcs.u8())
                .serialize(Array.from(imageBlobBytes))
                .toBytes();

            const creatorNameBCS = bcs.string().serialize(creatorName).toBytes();
            const titleBCS = bcs.string().serialize(title).toBytes();

            const parentBCS = bcs.u64().serialize(BigInt(parent)).toBytes();
            const priceBCS = bcs.u64().serialize(BigInt(price)).toBytes();

            // Now build the moveCall transaction
            txb.setSender(keypair.getPublicKey().toSuiAddress());

            txb.moveCall({
                target: `${AI_GAME_GENERATOR_PACKAGE_ID}::ai_game_generator::create_game_shared`,
                arguments: [
                    txb.object(GAME_BOOK_OBJECT_ID),
                    txb.pure(blobBytesBCS), // vector<u8>
                    txb.pure(creatorNameBCS), // string
                    txb.pure(titleBCS), // string
                    txb.pure(imageBlobBytesBCS), // vector<u8>
                    txb.pure(parentBCS), // u64
                    txb.pure(priceBCS), // u64
                ],
                typeArguments: [],
            });

            console.log("Transaction block prepared. Signing and executing...");

            const builtTx = await txb.build({ client: suiClient });

            const txnRes = await suiClient.signAndExecuteTransaction({
                signer: keypair,
                transaction: builtTx, // ✅ This is a Uint8Array
                options: {
                    showEffects: true,
                },
            });

            console.log("Transaction Response:", txnRes);

            if (txnRes?.digest) {
                console.log("Game creation successful. Digest:", txnRes.digest);
                setTxnDigest(txnRes.digest);
                setShowMintForm(false); // Hide the form after successful minting
            } else {
                throw new Error("Transaction failed or digest not found in response.");
            }
        } catch (err) {
            console.error("Error creating game:", err);
            const errorMessage =
                err instanceof Error
                    ? err.message
                    : String(err) ?? "An unknown error occurred.";
            setError(`Failed to create game: ${errorMessage}`);
        }
    };

    const handleFeedbackSubmit = async () => {
        if (!feedbackPrompt.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const response = await fetch("http://127.0.0.1:5000/update_game", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    feedbackPrompt: feedbackPrompt,
                    gameHtml: gameHtml,
                }),
            });
            if (response.ok) {
                const data = await response.json();
                console.log(data);
                setGameHtml(data.html);
                setLoading(false);
            } else {
                const errorText = await response.text();
                console.error("Backend error:", errorText);
            }
        } catch (err) {
            setError("Failed to update game. Please try again.");
            setLoading(false);
        }
    };
    return (
        <div>
            {gameHtml && (
                <>
                    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                        <h2 className="text-xl font-bold mb-4">{game.title}</h2>

                        <div className="border border-gray-300 rounded-lg mb-6 overflow-hidden">
                            <iframe
                                srcDoc={gameHtml}
                                title="Game Preview"
                                className="w-full h-160 border-0"
                                sandbox="allow-scripts allow-same-origin"
                                allow="autoplay"
                                onLoad={() => {
                                    document.querySelector("iframe").focus();
                                }}
                            />
                        </div>

                        <div className="flex flex-col md:flex-row gap-4">
                            <div className="flex-1">
                                <textarea
                                    className="w-full p-4 border border-gray-300 rounded-lg h-20"
                                    placeholder="Describe any changes you'd like to make to your game..."
                                    value={feedbackPrompt}
                                    onChange={(e) => setFeedbackPrompt(e.target.value)}
                                />
                            </div>
                            <div className="flex items-end">
                                <button
                                    className="px-6 py-3 bg-blue-600 text-white rounded-lg flex items-center hover:bg-blue-700 transition disabled:bg-gray-400"
                                    onClick={handleFeedbackSubmit}
                                    disabled={loading || !feedbackPrompt.trim()}
                                >
                                    {loading ? "Updating..." : "Update Game"}
                                </button>
                            </div>
                        </div>
                    </div>

                    {!showMintForm ? (
                        <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-lg shadow-md p-6 text-white">
                            <div className="flex flex-col md:flex-row justify-between items-center">
                                <div>
                                    <h2 className="text-xl font-bold mb-2">
                                        Ready to mint your game?
                                    </h2>
                                    <p className="opacity-80 mb-4 md:mb-0">
                                        Minting will require some SUI tokens as fees. Your game will
                                        be stored on the Sui blockchain.
                                    </p>
                                </div>
                                <button
                                    className="px-8 py-4 bg-white text-emerald-700 font-bold rounded-lg hover:bg-emerald-50 transition"
                                    onClick={handleShowMintForm}
                                >
                                    Prepare to Mint
                                </button>
                            </div>
                        </div>
                    ) : (
                        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                            <h2 className="text-xl font-bold mb-4">Mint Your Game</h2>
                            <p className="text-gray-600 mb-4">
                                Please provide your creator information to mint your game on the
                                Sui blockchain.
                            </p>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Creator Name
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                        placeholder="Enter your creator name"
                                        value={creatorName}
                                        onChange={(e) => setCreatorName(e.target.value)}
                                        required
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Game Title
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full p-3 border border-gray-300 rounded-lg"
                                        placeholder="Enter game title"
                                        value={title}
                                        onChange={(e) => setTitle(e.target.value)}
                                    />
                                </div>
                            </div>

                            <div className="flex justify-between items-center">
                                <button
                                    className="px-6 py-3 bg-gray-400 text-white rounded-lg hover:bg-gray-500 transition"
                                    onClick={() => setShowMintForm(false)}
                                >
                                    Cancel
                                </button>
                                <button
                                    className="px-8 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2 disabled:bg-gray-400"
                                    onClick={handleMint}
                                    disabled={loading || !creatorName.trim()}
                                >
                                    {loading ? "Minting..." : "Mint Game"}
                                </button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </div>
    );
};

export default Remix;
